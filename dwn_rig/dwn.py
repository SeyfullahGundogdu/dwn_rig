import aiohttp
import asyncio
import json
import os
import urllib.request
import argparse
import sys
import signal
import math
import re
import threading

# Define the default values
default_download_folder = "downloads"
default_subreddit = "wallpaper"
shutdown_requested = False
redgif_enabled = False
default_query= ""

#Gracefully handle SIGINT
def signal_handler(sig, frame):
    global shutdown_requested
    print("\nReceived SIGINT, program will finish processing the latest posts and stop.")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)

# Define a Filter class for resolution and/or aspect_ratio of images
class Filter:
    def __init__(self, width=None, height=None, ar_enabled=False):
        self.width = width
        self.height = height
        self.ar_enabled = ar_enabled


# Function to fetch data from a URL
async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.json()


# Function to download images and save them to a folder, inside our root download location
async def download_media(url, download_folder, folder_name, index=None):
    post_folder = os.path.join(download_folder, folder_name)
    os.makedirs(post_folder, exist_ok=True)
    if index != None:
        # if index is supplied it's zero based, 
        # that's why we are increasing it by one
        filename = os.path.join(post_folder, "{:02d}_".format(index+1)+url.split('/')[-1].split('?')[0])
    else:
        filename = os.path.join(post_folder, url.split('/')[-1].split('?')[0])
    
    # already downloaded the file
    if os.path.exists(filename):
        print(f"{filename} skipped.")
        return
    try:
        urllib.request.urlretrieve(url, filename)
    except Exception as e:
        return


# Function to download from a post that has multiple images
async def download_gallery(gallery_data, download_folder, filter, folder_name):
    global redgif_enabled
    #get the gallery images in order from here
    try:
        media_data = gallery_data['data']['gallery_data']['items']
        # Get every image link
        if filter:
            # there is a filter
            if filter.ar_enabled:
                # and it's by aspect ratio
                media_urls = []
                for (i, child) in enumerate(media_data):
                    media_id = child['media_id']
                    w = gallery_data['data']["media_metadata"][media_id]['s']['x']
                    h = gallery_data['data']["media_metadata"][media_id]['s']['y']
                    post_ar = calculate_aspect_ratio(w,h)
                    filter_ar = (filter.width, filter.height)
                    if post_ar == filter_ar:
                        media_urls.append(i, (gallery_data['data']["media_metadata"][child['media_id']]['s']['u']))
            else:
                # it's by resolution
                media = [(i, gallery_data['data']["media_metadata"][media_data[i]['media_id']]['s']) for i in range(len(media_data))]
                media_urls = [(child[0], child[1]['u']) for child in media if child[1]['x'] == filter.width and child[1]['y'] == filter.height]
        else:
            #there is no filter
            media_urls = [(i, gallery_data['data']["media_metadata"][media_data[i]['media_id']]['s']['u']) for i in range(len(media_data))]
        for (index, url) in media_urls:
            if not redgif_enabled and "redgif" in url:
                return
            await download_media(url, download_folder, folder_name, index=index)
    
    except Exception as e:
        # some images' media_metadata status can be a non-valid value, eg failed
        # we just ignore them instead of filtering in the above try block
        return

#calculates aspect ratio of images,
# 16:9 for 1920x1080
# 2:1, or 18:9 for 1800x900 images etc.
def calculate_aspect_ratio(w, h):
    divisor = math.gcd(w, h)
    w_r = w // divisor
    h_r = h // divisor

    return w_r, h_r

# Function to filter and get a single image from a post
async def filter_and_download_media(child, filter, download_folder, folder_name):
    global redgif_enabled
    # check if there is a resolution filter
    try:
        if filter:
            w = child['data']['preview']['images'][0]['source']['width']
            h = child['data']['preview']['images'][0]['source']['height']
            # it's by aspect ratio, 16:9, 18:9, 21:9 etc.
            if filter.ar_enabled:
                post_ar = calculate_aspect_ratio(w,h)
                filter_ar = (filter.width, filter.height)
                if post_ar != filter_ar:
                    return
            # it's by direct resolution 1920x1080 etc.
            elif w != filter.width or h != filter.height:
                return

        # Redgif is banned in some countries and it hangs indefinitely upon sending a request
        if not redgif_enabled and "redgif" in child['data']['url_overridden_by_dest']:
            return    
        media_url = child['data']['url_overridden_by_dest']
        await download_media(media_url, download_folder, folder_name)
    except Exception as e:
        return

# Function to process each post
async def process_post(child, filter, download_folder):
    # Shorten title because Linux has limitations on long folder names
    post_title = re.sub(r'[^a-zA-Z\s]', '', child['data']['title'][0:25]).replace(" x", '').strip()
    # Post is a gallery, meaning there are multiple images
    if 'is_gallery' in child['data'] and child['data']['is_gallery']:
        await download_gallery(child, download_folder, filter, post_title)
    # Single image in post
    else:
        await filter_and_download_media(child, filter, download_folder, post_title)

# Wrapper function to download posts in a multithreaded environment.
def posts_wrapper(child, i, latest_index, filter, download_folder, index_lock):
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_post(child, filter, download_folder))
    loop.close()
    with index_lock:
        # current post's index is greater than the latest, update latest_index
        if i > latest_index[0]: # cheating by using a list and making python pass by reference
            latest_index[0] = i

async def get_posts(session, url, after_value, filter, download_folder):
    global shutdown_requested
    try:
        # We have an after value, use it as an anchor point to get posts
        if len(after_value) > 0:
            url_with_after = f"{url}&after={after_value}"
        # after_value is empty, don't change the URL
        else:
            url_with_after = url

        data = await fetch_data(session, url_with_after)
        children = data['data']['children']
        if len(children) == 0:
            print("No posts found.")
            exit(0)
        # make a lock for preventing data race when saving the latest post processed.
        # used an array with 1 element, that way we will use the variable by reference instead of value     
        index_lock = threading.Lock()
        latest_index = [0]

        threads = []
        # Each child is a post in the subreddit
        # download each post in its own thread.
        for (i, child) in enumerate(children):
            # I used removal_reason value for checking if a post was removed or not
            # I don't know any better way to concretely tell if a post is removed from reddit.
            if child['data']['removal_reason'] != None:
                continue
            # If something goes wrong and request fails, we skip this post and go to older posts
            # can't use async functions when starting a thread, that's why we use a wrapper function
            t = threading.Thread(target=posts_wrapper, args=(child, i, latest_index, filter, download_folder, index_lock))
            t.start()
            threads.append(t)
            
            if shutdown_requested:
                # Stop processing other posts.
                break
        #join worker threads to our main thread.
        for t in threads:
            t.join()
        # return the latest post's name.
        after_value = children[latest_index[0]]['data']['name']    
        return after_value

    except Exception as e:
        # No need to print exception, 
        # just skip the problematic post by saving its name 
        return after_value


# Main function
async def main(args):
    global shutdown_requested
    global redgif_enabled

    download_folder = args.download_folder
    subreddit_name = args.subreddit_name
    resolution = args.resolution
    aspect_ratio = args.aspect_ratio
    redgif_enabled = args.enable_redgif
    query = args.query

    # Subreddit URL for downloading images and gifs
    if query:
        url = f"https://www.reddit.com/r/{subreddit_name}/search.json?limit=10&raw_json=1&restrict_sr=true&q={query}"
    else:
        url = f"https://www.reddit.com/r/{subreddit_name}/top.json?t=year&limit=10&raw_json=1"
    # Check if root download folder exists
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    # Default after_value is empty, meaning we just start from the last posts in the subreddit
    after_value = ""

    # File name to read from and write to
    after_file = os.path.join(download_folder, "after")

    # Check if after_file exists, if so read it to after_value
    if os.path.exists(after_file):
        after_value = open(after_file, 'r').read()

    # construct filter instance
    if resolution:         # width          height
        filter = Filter(resolution[0], resolution[1], False)
    elif aspect_ratio:
        w_r, h_r = calculate_aspect_ratio(aspect_ratio[0], aspect_ratio[1])
        filter = Filter(w_r, h_r, True)
    else:
        filter = None
    # Let it rip
    async with aiohttp.ClientSession() as session:
        # Pretty naive loop
        # Don't kill the program when it's writing to file at the end of each iteration
        # I want to make it listen to signals and stop itself gracefully at some point
        while not shutdown_requested:
                # Get new anchor point, write to file and use that point again to search for older posts
                after_value = await get_posts(session, url, after_value, filter, download_folder)
                # Save the latest post we found
                with open(after_file, 'w') as af:
                    af.seek(0)
                    af.write(after_value)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Download images from a subreddit")
    # Add arguments for download_folder and subreddit_name
    parser.add_argument("-df", "--download-folder", default=default_download_folder, metavar="folder",
                        help="Root folder of saved posts (default: downloads).")
    parser.add_argument("-sn", "--subreddit-name", default=default_subreddit, metavar="subreddit",
                        help="Subreddit name for downloading images (default: wallpapers).")
    # Add mutually exclusive group for filtering by resolution, or aspect ratio 
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--resolution", nargs=2, type=int, metavar=('width', 'height'),
                        help="Filter images by resolution e.g., --resolution 1920 1080. No resolution filter by default.")
    group.add_argument("-ar", "--aspect-ratio", nargs=2, type=int, metavar=('width','height'),
                        help="Filter images by aspect ratio e.g., -ar 16 9. No aspect ratio filter by default.")

    # Add text filter
    parser.add_argument("-q", "--query", default=default_query, metavar="query",
                        help="Search query for searching posts.")
    # Check if redgif links are enabled
    group.add_argument("-eg", "--enable-redgif", default=redgif_enabled, action="store_true",
                        help="Enable redgif links, by default they are disabled because it's banned in some countries.")
    
    args = parser.parse_args()
    print(f"Started downloading media to the current directory, check the {args.download_folder} folder.")
    # Run the main function with command-line arguments
    asyncio.run(main(args))
    print(f"Latest post number saved in {args.download_folder}/after")

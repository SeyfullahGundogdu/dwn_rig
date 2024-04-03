import aiohttp
import asyncio
import json
import os
import urllib.request
import argparse
import sys
import signal
import math

# Define the default values
default_download_folder = "downloads"
default_subreddit = "wallpapers"
shutdown_requested = False
redgif_enabled = False

#Gracefully handle SIGINT
def signal_handler(sig, frame):
    global shutdown_requested
    print("\nReceived SIGINT, program will finish processing the current post and stop.")
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
async def download_media(url, download_folder, folder_name):
    download_folder = os.path.join(download_folder, folder_name)
    os.makedirs(download_folder, exist_ok=True)
    filename = os.path.join(download_folder, url.split('/')[-1].split('?')[0])
    urllib.request.urlretrieve(url, filename)


# Function to download from a post that has multiple images
async def download_gallery(gallery_data, download_folder, folder_name, filter):
    # Get every image link
    if filter:
        # there is a filter
        if filter.ar_enabled:
            # and it's by aspect ratio
            w = child['s']['x']
            h = child['s']['y']
            post_ar = calculate_aspect_ratio(w,h)
            filter_ar = (filter.width, filter.height)
            media_urls = [child['s']['u'] for child in gallery_data.values() if post_ar == filter_ar]
        else:
            #it's by resolution
            media_urls = [child['s']['u'] for child in gallery_data.values() if child['s']['x'] == filter.width and child['s']['y'] == filter.height]
    else:
        #there is no filter
        media_urls = [child['s']['u'] for child in gallery_data.values()]
    
    for url in media_urls:
        if not redgif_enabled and "redgif" in url:
            return
        await download_media(url, download_folder, folder_name)

#calculates aspect ratio of images,
# 16:9 for 1920x1080
# 2:1, or 18:9 for 1800x900 images etc.
def calculate_aspect_ratio(w, h):
    divisor = math.gcd(w, h)
    w_r = w // divisor
    h_r = h // divisor

    return w_r, h_r

# Function to filter and get a single image from a post
async def filter_and_download_media(child, filter, download_folder):
    # there is a filter
    if filter:
        w = int(child['data']['preview']['images'][0]['source']['width'])
        h = int(child['data']['preview']['images'][0]['source']['height'])
        # it's by aspect ratio, 16:9, 18:9, 21:9 etc.
        if filter.ar_enabled:
            post_ar = calculate_aspect_ratio(w,h)
            filter_ar = (filter.width, filter.height)
            if post_ar != filter_ar:
                return
        # it's by direct resolution 1920x1080 etc.
        elif width != filter.width or height != filter.height:
            return

    media_url = child['data']['url_overridden_by_dest']
    # Redgif is banned in some countries and it hangs indefinitely upon sending a request
    if not redgif_enabled and "redgif" in media_url:
        return
    # Shorten title because Linux has limitations on long folder names
    title = child['data']['title'][0:25]
    # Sanitize title and download a single image to the folder
    folder_name = title.replace('/', '-')
    await download_media(media_url, download_folder, folder_name)


# Function to process each post
async def process_post(child, filter, download_folder):
    # Post is a gallery, meaning there are multiple images
    if 'is_gallery' in child['data'] and child['data']['is_gallery']:
        title = child['data']['title'][0:25].replace('/', '-')
        await download_gallery(child['data']['media_metadata'], download_folder, title, filter)
    # Single image in post
    else:
        await filter_and_download_media(child, filter, download_folder)


async def get_posts(session, url, after_value, filter, download_folder):
    global shutdown_requested
    try:
        # We have an after value, use it as an anchor point to get posts
        if len(after_value) > 0:
            url_with_after = f"{url}&after={after_value}"
        # After_value is empty, don't change the URL
        else:
            url_with_after = url

        data = await fetch_data(session, url_with_after)
        # Each child is a post in the subreddit
        for child in data['data']['children']:
            # Save each post's name as our anchor at the start
            # If something goes wrong and request fails, we skip this post and go to older posts
            # I don't know what happens if the try block fails before this point though.
            after_value = child['data']['name']
            await process_post(child, filter, download_folder)
            # Stop reading other posts, save current post and stop the program
            if shutdown_requested:
                break

        return after_value

    except Exception as e:
        # No need to print exception, 
        # just skip the problematic post by saving its name 
        return after_value


# Main function
async def main(args):
    global shutdown_requested

    download_folder = args.download_folder
    subreddit_name = args.subreddit_name
    resolution = args.resolution
    aspect_ratio = args.aspect_ratio
    redgif_enabled = args.enable_redgif

    # Subreddit URL for downloading images and gifs
    url = f"https://www.reddit.com/r/{subreddit_name}.json?limit=100&raw_json=1"
    
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
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Download images from a subreddit")
    # Add arguments for download_folder and subreddit_name
    parser.add_argument("-df", "--download-folder", default=dwn.default_download_folder, metavar="folder",
                        help="Root folder of saved posts (default: downloads).")
    parser.add_argument("-sn", "--subreddit-name", default=dwn.default_subreddit, metavar="subreddit",
                        help="Subreddit name for downloading images (default: wallpapers).")
    # Add mutually exclusive group for filtering by resolution, or aspect ratio 
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--resolution", nargs=2, type=int, metavar=('width', 'height'),
                        help="Filter images by resolution e.g., --resolution 1920 1080. No resolution filter by default.")
    group.add_argument("-ar", "--aspect-ratio", nargs=2, type=int, metavar=('width','height'),
                        help="Filter images by aspect ratio e.g., -ar 16 9. No aspect ratio filter by default.")

    # Check if redgif links are enabled
    group.add_argument("-eg", "--enable-redgif", default=dwn.redgif_enabled, action="store_true",
                        help="Enable redgif links, by default they are disabled because it's banned in some countries.")
    
    args = parser.parse_args()
    print(f"Started downloading media to the current directory, check the {args.download_folder} folder.")
    # Run the main function with command-line arguments
    asyncio.run(dwn.main(args))
    print(f"Latest post number saved to in {args.download_folder}/after")

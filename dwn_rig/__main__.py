import asyncio
import argparse
from dwn_rig import dwn

if __name__ == "__main__":
    main()

def main():
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

    # Add text filter
    parser.add_argument("-q", "--query", default=dwn.default_query, metavar="query",
                        help="Search query for searching posts.")
    # Check if redgif links are enabled
    group.add_argument("-eg", "--enable-redgif", default=dwn.redgif_enabled, action="store_true",
                        help="Enable redgif links, by default they are disabled because it's banned in some countries.")
    
    args = parser.parse_args()
    print(f"Started downloading media to the current directory, check the {args.download_folder} folder.")
    # Run the main function with command-line arguments
    asyncio.run(dwn.main(args))
    print(f"Latest post number saved in {args.download_folder}/after")

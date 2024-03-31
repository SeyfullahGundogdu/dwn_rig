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
                        help="Root folder of saved posts (default: downloads)")
    parser.add_argument("-sn", "--subreddit-name", default=dwn.default_subreddit, metavar="subreddit",
                        help="Subreddit name for downloading images (default: wallpapers)")
    parser.add_argument("-r", "--resolution", nargs=2, type=int, metavar=('width', 'height'),
                        help="Filter images by resolution e.g., --resolution 1920 1080. No filter by default, which means app will download every image etc. it can find.")
    # Parse command-line arguments
    args = parser.parse_args()

    print(f"Started downloading media to the current directory, check the {args.download_folder} folder.")
    # Run the main function with command-line arguments
    asyncio.run(dwn.main(args.download_folder, args.subreddit_name, args.resolution))
    print(f"Latest post number saved to in {args.download_folder}/after")

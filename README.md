# Download Images and GIFs from reddit posts

Simple python3 script for downloading images and GIFs from reddit.

## Warning
I don't know if you can be banned by reddit if you use this, 
we just use `reddit/r/sub_name.json` for getting posts. The program shouldn't send too many requests at a short time interval. But using a VPN is still recommended just to be safe.

## Getting Started
For now, program runs until it recieves a SIGINT, or until getting killed by other means.
This script depends on requests, aiohttp and configargparse libraries. If you are using nix and flakes are enabled, you can use flake.nix file to run the program directly:

```shell
nix run github:SeyfullahGundogdu/dwn_rig -- -h
```

If not, another option is to use [poetry](https://python-poetry.org/) to run the code.
Clone the repo:

```shell
git clone https://github.com/SeyfullahGundogdu/dwn_rig && cd dwn_rig
```
and then,

```shell
poetry run dwn-rig --help
```

Or you can just copy the dwn.py file and run traditionally.
Note: Don't forget to install dependencies.

```shell
git clone https://github.com/SeyfullahGundogdu/dwn_rig
cp ./dwn_rig/dwn_rig/dwn.py ./
python3 dwn.py -h
```
## CLI
There are currently 3 arguments, download-folder(downloads by default), subreddit-name(wallpapers by default, it's also case insensitive), and resolution (None by default):

> Note: if no resolution is specified, program will download every media file it finds on posts.


### Nix Flakes
You can add arguments to program by:

```shell
nix run github:SeyfullahGundogdu/dwn_rig -- --download-folder downloads --subreddit-name wallpapers
```

another example:

```shell
nix run github:SeyfullahGundogdu/dwn_rig -- --download-folder walls_archive --subreddit-name unixporn --resolution 1920 1080
```

for shorthand versions:

```shell
nix run github:SeyfullahGundogdu/dwn_rig -- -df downloads -sn wallpapers
# or 
nix run github:SeyfullahGundogdu/dwn_rig -- -df walls_archive -sn unixporn -r 1920 1080
```


### Poetry
Remember to clone the repo. At the project's root directory:

```shell
poetry run dwn-rig -df my_wallpaper_archive -sn wallpapers -r 1920 1080
# or
poetry run dwn-rig --download-folder archive_folder -sn wallpapers --resolution 1920 1080
```

### Python
get dwn.py file from the repo and then:
```shell
python dwn.py -df my_wallpaper_archive -sn wallpapers -r 1920 1080
# or
python dwn.py --download-folder archive_folder -sn wallpapers --resolution 1920 1080
```
## TODO

- [ ] Implement filter by aspect ratio (16:9, 21:9 etc.).
- [ ] Implement more, better filters.
- [ ] Better parsing the json for good error handling.
- [ ] RiiR at some point.
- [ ] Maybe add a GUI idk.
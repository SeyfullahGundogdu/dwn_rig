# Download Images and GIFs from reddit posts

Simple python3 script for downloading images and GIFs from reddit, now with multithreading support.

## Getting Started
For now, program runs until it recieves a SIGINT, or until getting killed by other means.
This script depends on some third party libraries. Check the pyproject.toml file for their list. If you are using nix and flakes are enabled, you can use flake.nix file to run the program directly:

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
Keep reading for examples on how to supply arguments correctly to the program.

> Note: if no specific resolution or aspect ratio is specified, program will download every media file it finds on posts.


### Nix Flakes
You can add arguments to program by:


```shell
# download every media you can find, no filter but redgif links disabled
nix run github:SeyfullahGundogdu/dwn_rig -- --download-folder downloads --subreddit-name wallpaper
```

another example:

```shell
# download to walls_archive folder, get posts from unixporn subreddit
# filter by aspect ratio (16:9), redgif links are disabled
nix run github:SeyfullahGundogdu/dwn_rig -- --download-folder walls_archive --subreddit-name unixporn --aspect-ratio 16 9
```

for examples with shorthand versions of some arguments:

```shell
nix run github:SeyfullahGundogdu/dwn_rig -- -df downloads -sn wallpaper
# or 
nix run github:SeyfullahGundogdu/dwn_rig -- -df walls_archive -sn unixporn -r 1920 1080 -eg # -eg is for enabling redgif links
# yet another example using "space" as query:
nix run github:SeyfullahGundogdu/dwn_rig -- -df wallpaper_archive -sn wallpaper -q space
# or you want some sway themes:
nix run github:SeyfullahGundogdu/dwn_rig -- -df sway_archive -sn unixporn -q sway
```

### Poetry
Remember to clone the repo. At the project's root directory:

```shell
# read help text
poetry run dwn-rig -h
# or go right into action
poetry run dwn-rig -df my_wallpaper_archive -sn wallpaper -r 1920 1080
# another one
poetry run dwn-rig --download-folder archive_folder -sn wallpaper --aspect-ratio 21 9 # for ultrawide monitors
```

### Python (Not Tested)
You can copy dwn.py file from the repo and then, as an example:
```shell
# read help text
python dwn.py -h
# and then
python dwn.py -df my_wallpaper_archive -sn wallpaper -r 1920 1080
# another example that uses "nature" as query string
python dwn.py --download-folder archive_folder -sn wallpaper -ar 18 9 -q nature -eg
```
## TODO

- [X] Implement filter by aspect ratio (16:9, 21:9 etc.).
- [X] Add search filter for posts.
- [ ] Implement more, better filters.
- [ ] Better parsing the json for good error handling.
- [ ] RiiR at some point.
- [ ] Maybe add a GUI idk.
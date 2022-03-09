## IMPORTANT NOTICE: up until 2022-03-09, the package was called itchio, it is now called itchiodl (to avoid pypi conflicts)

# Itchio Downloader Tool
## Install
```bash
pip install itchiodl
```
## Download All Games in library from account

```bash

python -m itchiodl.downloader

# via setup-tools entry point
itch-download
```

This uses the same API the itchio app uses to download the files. If you have 2FA enabled, generate an API key [here](https://itch.io/user/settings/api-keys) and run the following instead

```bash
# via python
python -m itchiodl.downloader --api-key=KEYHERE

# via setup-tools entry point
itch-download -k KEYHERE
```

## Add All Games in a bundle to your library

```bash
# via python
python -m itchiodl.bundle_tool

# via setup-tools entry point
itch-load-bundle
```

This is a bit of a bodge, but it works. It essentially goes through and clicks the "Download" link on every item on the bundle's page, which adds it to your itchio library. It does not download any files. You will need the download page's URL (this will be in the bundle's email, and possibly your purchase history). It will not work with 2FA, and I'm unlikely to be able to fix it without making it far more complicated


## Errors
if a download fails it will be reported in ```errors.txt``` in the same directory as your downloads

An example of which could look something like this:
```Cannot download game/asset: <Game Name>
Publisher Name: <Publisher Name>
Output File: <Publisher Name>/<Game Name>/<Specific Item>
Request URL: <Some URL>
Request Response Code: 404
Error Reason: Not Found
This game/asset has been skipped please download manually
---------------------------------------------------------
```

This is not a perfect solution but does prevent the whole process from crashing

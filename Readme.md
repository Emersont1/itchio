## IMPORTANT NOTICE: up until 2022-03-09, the package was called itchio, it is now called itchiodl (to avoid pypi conflicts)

# Itchio Downloader Tool
## Install
```bash
pip install itchiodl
```
## Download All Games in library from account
**Please Note:** Having too many jobs may cause rate-limiting from some testing 8 works fine but 10 starts giving errors.

```bash
# via python
python -m itchiodl.downloader

# via setup-tools entry point
itch-download
```

This uses the same API the itchio app uses to download the files. If you have 2FA enabled, generate an API key [here](https://itch.io/user/settings/api-keys) and run the following instead

```bash
# via python (with 4 concurrent downloads)
python -m itchiodl.downloader --api-key=KEYHERE --jobs=4

# via setup-tools entry point
itch-download -k KEYHERE

# download with multiple threads, default is 4 if unspecified
itch-download -k KEYHERE -j 4

# only download osx or cross platform downloads
itch-download -p osx

# folder structure uses display names for users/publishers and game titles
itch-download -vf

# skips downloads above a certain size in megabytes, supports decimals
itch-download -sas 50.0

# Disables file verification entirely, files with the same name are assumed to be the same file
itch-download --no-verify

# Disables writing supplementary .md5 files, existing files will still be hashed against their download hashes
# Does nothing if --no-verify is specified
itch-download --no-verify-file

# Downloads all free titles from the specified publisher
# Argument should be formatted 'https://{publisher}.itch.io'
itch-download --download-publisher

# Checks if title is owned, then downloads all files for it
# Argument should be formatted 'https://{publisher}.itch.io/{title}/'
itch-download --download-game

# For the --download-game argument, skips the check to see if the title is currently owned
# In practice this downloads free files only
itch-download --skip-library-load
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

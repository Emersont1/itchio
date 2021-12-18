# Itchio Downloader Tool
## Install
```bash
pip install git+https://github.com/emersont1/itchio 
```
## Download All Games in library from account

```bash
python -m itchio.downloader
```

This uses the same API the itchio app uses to download the files. If you have 2FA enabled, generate an API key [here](https://itch.io/user/settings/api-keys) and run the following instead

```bash
python -m itchio.downloader --api-key=KEYHERE
```

## Add All Games in a bundle to your library

```bash
python -m itchio.downloader
```

This is a bit of a bodge, but it works. It essentially goes through and clicks the "Download" link on every item on the bundle's page, which adds it to your itchio library. It does not download any files. You will need the download page's URL (this will be in the bundle's email, and possibly your purchase history). It will not work with 2FA, and I'm unlikely to be able to fix it without making it far more complicated

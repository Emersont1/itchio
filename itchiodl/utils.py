import re
import hashlib
import requests


class NoDownloadError(Exception):
    """No download found exception"""


def download(url, path, name, file):
    """Downloads a file from a url and saves it to a path, skips it if it already exists."""

    desc = f"{name} - {file}"
    print(f"Downloading {desc}")
    rsp = requests.get(url, stream=True)

    if (
        rsp.headers.get("content-length") is None
        or rsp.headers.get("Content-Disposition") is None
    ):
        raise NoDownloadError("Http response is not a download, skipping")

    cd = rsp.headers.get("Content-Disposition")

    filename_re = re.search(r'filename="(.+)"', cd)
    if filename_re is None:
        filename = file
    else:
        filename = filename_re.group(1)

    with open(f"{path}/{filename}", "wb") as f:
        for chunk in rsp.iter_content(10240):
            f.write(chunk)

    print(f"Downloaded {filename}")
    return f"{path}/{filename}", True


def clean_path(path):
    """Cleans up invalid filename characters"""
    path_clean = re.sub(r"[<>:|?*\"\/\\]", "-", path)
    # This checks for strings that end in ... or similar,
    # weird corner case that affects fewer than 0.1% of titles
    path_clean = re.sub(r"(.)[.]\1+$", "-", path_clean)
    return path_clean


def md5sum(path):
    """Returns the md5sum of a file"""
    md5 = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

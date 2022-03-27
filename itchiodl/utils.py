import requests
import re
import os
import sys

from clint.textui import progress


class NoDownloadError(Exception):
    pass


def download(url, path, name, file):
    """Downloads a file from a url and saves it to a path, skips it if it already exists."""

    desc = f"{name} - {file}"
    print(f"Downloading {desc}")
    rsp = requests.get(url, stream=True)

    if rsp.headers.get(
            'content-length') is None or rsp.headers.get("Content-Disposition") is None:
        raise NoDownloadError("Http response is not a download, skipping")

    cd = rsp.headers.get("Content-Disposition")

    filename_re = re.search(r'filename="(.+)"', cd)
    if filename_re is None:
        filename = file
    else:
        filename = filename_re.group(1)

    total_length = int(rsp.headers.get('content-length'))

    if os.path.exists(f"{path}/{filename}"):
        if os.path.getsize(f"{path}/{filename}") == total_length:
            print(f"{filename} already exists, skipping")
            return f"{path}/{filename}", False
        else:
            print(f"{filename} exists but is incomplete, downloading again")

    with open(f"{path}/{filename}", "wb") as f:
        for chunk in progress.bar(
            rsp.iter_content(
                chunk_size=1024), expected_size=(
                total_length / 1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()
    return f"{path}/{filename}", True


def clean_path(path):
    """Cleans a path on windows"""
    if sys.platform in ["win32", "cygwin", "msys"]:
        path_clean = re.replace(r'[\<\>\:\"\/\\\|\?\*]', "-", path)
        return path_clean
    return path


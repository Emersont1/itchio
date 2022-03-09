import requests
import re
import os

from clint.textui import progress


class NoDownloadError(Exception):
    pass


def download(url, path, desc):
    print(f"Downloading {desc}")
    rsp = requests.get(url, stream=True)

    if rsp.headers.get(
            'content-length') is None or rsp.headers.get("Content-Disposition") is None:
        raise NoDownloadError("Http response is not a download, skipping")

    cd = rsp.headers.get("Content-Disposition")
    filename = re.search(r'filename="(.+)"', cd).group(1)
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

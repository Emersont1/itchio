import re
import json
import os
import urllib
import datetime
import shutil
import requests


import itchiodl.utils


class Game:
    """Representation of a game download"""

    def __init__(self, data):
        self.data = data["game"]
        self.name = itchiodl.utils.clean_path(self.data["title"])
        self.publisher = self.data.get("user").get("display_name")
        if not self.publisher:
            self.publisher = self.data.get("user").get("username")
        self.link = self.data["url"]

        matches = re.match(r"https://(.+)\.itch\.io/(.+)", self.link)
        self.game_slug = matches.group(2)
        self.publisher_slug = itchiodl.utils.clean_path(self.publisher)

        #if "VerboseFolders" in globals():
        #    self.destination_folder = self.game_slug if not VerboseFolders else self.name
        #else:
        #    self.destination_folder = self.game_slug
        #    print("VerboseFolders Not Detected in Global Variables, Falling Back to Game Slug\n")
        self.destination_path = os.path.normpath(f"{self.publisher_slug}/{self.name}")

        self.files = []
        self.downloads = []

    def load_downloads(self, token):
        """Load all downloads for this game"""
        self.downloads = []
        if self.id:
            r = requests.get(
                f"https://api.itch.io/games/{self.game_id}/uploads?download_key_id={self.id}",
                headers={"Authorization": token},
            )
        else:
            r = requests.get(
                f"https://api.itch.io/games/{self.game_id}/uploads",
                headers={"Authorization": token},
            )
        j = r.json()
        for d in j["uploads"]:
            self.downloads.append(d)

    def download(self, token, platform):
        """Download a singular file"""
        print("Downloading", self.name)

        self.load_downloads(token)

        if not os.path.exists(self.destination_path):
            os.makedirs(self.destination_path)

        for d in self.downloads:
            if (
                platform is not None
                and d["traits"]
                and f"p_{platform}" not in d["traits"]
            ):
                print(f"Skipping {self.name} for platform {d['traits']}")
                continue
            self.do_download(d, token)

        with open(f"{self.destination_path}.json", "w") as f:
            json.dump(
                {
                    "name": self.name,
                    "publisher": self.publisher,
                    "link": self.link,
                    "game_id": self.game_id,
                    "itch_data": self.data,
                },
                f,
                indent=2,
            )

    def do_download(self, d, token):
        """Download a single file, checking for existing files"""
        print(f"Downloading {d['filename']}")

        file = itchiodl.utils.clean_path(d["filename"] or d["display_name"] or d["id"])
        path = self.destination_path

        if os.path.exists(f"{path}/{file}"):
            print(f"File Already Exists! {file}")
            if os.path.exists(f"{path}/{file}.md5"):

                with open(f"{path}/{file}.md5", "r") as f:
                    md5 = f.read().strip()

                    if md5 == d["md5_hash"]:
                        print(f"Skipping {self.name} - {file}")
                        return
                    print(f"MD5 Mismatch! {file}")
            else:
                md5 = itchiodl.utils.md5sum(f"{path}/{file}")
                if md5 == d["md5_hash"]:
                    print(f"Skipping {self.name} - {file}")

                    # Create checksum file
                    with open(f"{path}/{file}.md5", "w") as f:
                        f.write(d["md5_hash"])
                    return
                # Old Download or corrupted file?
                corrupted = False
                if corrupted:
                    os.remove(f"{path}/{file}")
                    return

            if not os.path.exists(f"{path}/old"):
                os.mkdir(f"{path}/old")

            print(f"Moving {file} to old/")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            print(timestamp)
            shutil.move(f"{path}/{file}", f"{path}/old/{timestamp}-{file}")

        # Get UUID
        r = requests.post(
            f"https://api.itch.io/games/{self.game_id}/download-sessions",
            headers={"Authorization": token},
        )
        j = r.json()

        # Download
        if self.id:
            url = (
                f"https://api.itch.io/uploads/{d['id']}/"
                + f"download?api_key={token}&download_key_id={self.id}&uuid={j['uuid']}"
            )
        else:
            print("!! NO DOWNLOAD KEY !!")
            url = (
                f"https://api.itch.io/uploads/{d['id']}/"
                + f"download?api_key={token}&uuid={j['uuid']}"
            )
        # response_code = urllib.request.urlopen(url).getcode()
        try:
            itchiodl.utils.download(url, path, self.name, file)
        except itchiodl.utils.NoDownloadError:
            print("Http response is not a download, skipping")

            with open("errors.txt", "a") as f:
                f.write(
                    f""" Cannot download game/asset: {self.game_slug}
                    Publisher Name: {self.publisher_slug}
                    Path: {path}
                    File: {file}
                    Request URL: {url}
                    This request failed due to a missing response header
                    This game/asset has been skipped please download manually
                    ---------------------------------------------------------\n """
                )

            return
        except urllib.error.HTTPError as e:
            print("This one has broken due to an HTTP error!!")

            with open("errors.txt", "a") as f:
                f.write(
                    f""" Cannot download game/asset: {self.game_slug}
                    Publisher Name: {self.publisher_slug}
                    Path: {path}
                    File: {file}
                    Request URL: {url}
                    Request Response Code: {e.code}
                    Error Reason: {e.reason}
                    This game/asset has been skipped please download manually
                    ---------------------------------------------------------\n """
                )

            return

        # Verify
        #if itchiodl.utils.md5sum(f"{path}/{file}") != d["md5_hash"]:
        #    print(f"Failed to verify {file}")
        #    return

        # Create checksum file
        #with open(f"{path}/{file}.md5", "w") as f:
        #    f.write(d["md5_hash"])

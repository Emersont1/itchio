import copy
import re
import json
import os
import urllib
import datetime
import shutil
import requests


from itchiodl.utils import clean_path, md5sum, download, NoDownloadError


class Game:
    """Representation of a game download"""

    def __init__(self, data):
        self.data = data["game"]
        self.name = self.data["title"]
        self.publisher = self.data["user"]["username"]
        self.link = self.data["url"]
        if "game_id" in data:
            self.id = data["id"]
            self.game_id = data["game_id"]
        else:
            self.id = False
            self.game_id = self.data["id"]

        matches = re.match(r"https://(.+)\.itch\.io/(.+)", self.link)
        self.game_slug = matches.group(2)
        self.publisher_slug = matches.group(1)

        self.files = []
        self.downloads = []
        self.path = os.path.abspath(
            f"{clean_path(self.publisher_slug)}/{clean_path(self.game_slug)}")

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
        r.raise_for_status()
        j = r.json()
        self.downloads = copy.copy(j["uploads"])

    def download(self, token, platform):
        """Download a singular file"""
        print("Downloading", self.name)

        # if os.path.exists(f"{self.publisher_slug}/{self.game_slug}.json"):
        #    print(f"Skipping Game {self.name}")
        #    return

        self.load_downloads(token)

        os.makedirs(self.path, exist_ok=True)

        for d in self.downloads:
            if (
                platform is not None
                and d["traits"]
                and f"p_{platform}" not in d["traits"]
            ):
                print(f"Skipping {self.name} for platform {d['traits']}")
                continue
            self.do_download(d, token)

        with open("{self.path}.json", "w") as f:
            json.dump(
                {
                    "name": self.name,
                    "publisher": self.publisher,
                    "link": self.link,
                    "itch_id": self.id,
                    "game_id": self.game_id,
                    "itch_data": self.data,
                },
                f,
                indent=2,
            )

    def do_download(self, d, token):
        """Download a single file, checking for existing files"""
        print(f"Downloading {d['filename']}")

        file = clean_path(d["filename"] or d["display_name"] or d["id"])

        if os.path.exists(f"{self.path}/{file}"):
            print(f"File Already Exists! {file}")
            if os.path.exists(f"{self.path}/{file}.md5"):

                with open(f"{self.path}/{file}.md5", "r") as f:
                    md5 = f.read().strip()

                    if md5 == d["md5_hash"]:
                        print(f"Skipping {self.name} - {file}")
                        return
                    print(f"MD5 Mismatch! {file}")
            else:
                md5 = md5sum(f"{self.path}/{file}")
                if md5 == d["md5_hash"]:
                    print(f"Skipping {self.name} - {file}")

                    # Create checksum file
                    with open(f"{self.path}/{file}.md5", "w") as f:
                        f.write(d["md5_hash"])
                    return
                # Old Download or corrupted file?
                corrupted = False
                if corrupted:
                    os.remove(f"{self.path}/{file}")
                    return

            if not os.path.exists(f"{self.path}/old"):
                os.mkdir(f"{self.path}/old")

            print(f"Moving {file} to old/")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            print(timestamp)
            shutil.move(f"{self.path}/{file}", f"{self.path}/old/{timestamp}-{file}")

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
            url = (
                f"https://api.itch.io/uploads/{d['id']}/"
                + f"download?api_key={token}&uuid={j['uuid']}"
            )
        # response_code = urllib.request.urlopen(url).getcode()
        try:
            actual_destination = download(url, self.path, self.name, file)
        except NoDownloadError:
            print("Http response is not a download, skipping")

            with open("errors.txt", "a") as f:
                f.write(
                    f""" Cannot download game/asset: {self.game_slug}
                    Publisher Name: {self.publisher_slug}
                    Path: {self.path}
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
                    Path: {self.path}
                    File: {file}
                    Request URL: {url}
                    Request Response Code: {e.code}
                    Error Reason: {e.reason}
                    This game/asset has been skipped please download manually
                    ---------------------------------------------------------\n """
                )

            return

        # Verify
        if md5sum(actual_destination) != d["md5_hash"]:
            print(f"Failed to verify {file}{d}")
            return

        # Create checksum file
        with open(f"{actual_destination}.md5", "w") as f:
            f.write(d["md5_hash"])

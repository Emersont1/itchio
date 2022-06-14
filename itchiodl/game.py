import re
import json
import os
import urllib
import datetime
import shutil
import requests
import sys


import itchiodl.utils


class Game:
    """Representation of a game download"""

    def __init__(self, data):
        self.id = False
        self.game_id = None
        self.args = sys.argv[1:]
        if '-vf' in self.args or '--verbose-folders' in self.args:
            self.verbose = True
        else:
            self.verbose = False

        if '--no-verify-file' in self.args:
            self.verify_file = False
        else:
            self.verify_file = True

        if '--no-verify ' in self.args:
            self.verify = False
        else:
            self.verify = True

        if '-sas' in self.args:
            self.skipping_large_entries = True
            self.skipping_above_size_MB = float(self.args[(self.args.index('-sas')+1)])
            self.skipping_above_size_B = abs(self.skipping_above_size_MB * 1000000)
        elif '--skip-above-size' in self.args:
            self.skipping_large_entries = True
            self.skipping_above_size_MB = float(self.args[(self.args.index('--skip-above-size')+1)])
            self.skipping_above_size_B = abs(self.skipping_above_size_MB * 1000000)
        else:
            self.skipping_large_entries = False

        self.data = data["game"]

        self.link = self.data["url"]
        matches = re.match(r"https://(.+)\.itch\.io/(.+)", self.link)
        self.game_slug = matches.group(2)

        if self.verbose:
            self.name = itchiodl.utils.clean_path(self.data["title"])
            self.publisher = self.data.get("user").get("display_name")
            if not self.publisher:
                self.publisher = self.data.get("user").get("username")
        else:
            self.name = self.game_slug
            self.publisher = self.data.get("user").get("username")

        self.publisher_slug = itchiodl.utils.clean_path(self.publisher)

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
        if j.get("uploads") is None:
            j.update({"uploads": []})
        for d in j.get("uploads"):
            if d.get("size") is None:
                d.update({"size": 0})
            if not self.skipping_large_entries:
                self.downloads.append(d)
            elif self.skipping_above_size_B > d.get("size"):
                self.downloads.append(d)
            else:
                print(f"Skipping Large Item: {d.get('filename')}")

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
        print(f"Downloading `{d['filename']}`")

        file = itchiodl.utils.clean_path(d["filename"] or d["display_name"] or d["id"])
        path = self.destination_path
        if os.path.exists(f"{path}/{file}"):
            if self.verify:
                print(f"! `{file}` Already Exists!")
                if os.path.exists(f"{path}/{file}.md5"):
                    with open(f"{path}/{file}.md5", "r") as f:
                        md5 = f.read().strip()
                        if md5 == d.get("md5_hash"):
                            print(f"MD5 Hash Matches {self.name} - `{file}`, Skipping")
                            return
                        elif d.get("md5_hash") is None:
                            print("No MD5 Hash Supplied by Itch, assuming file is fine")
                            return
                        print(f"MD5 Mismatch! {file}")
                else:
                    md5 = itchiodl.utils.md5sum(f"{path}/{file}")
                    if md5 == d.get("md5_hash"):
                        print(f"MD5 Matches {self.name} - `{file}`, Skipping")
                        # Create checksum file
                        if self.verify_file:
                            with open(f"{path}/{file}.md5", "w") as f:
                                f.write(d["md5_hash"])
                        return
                    elif d.get("md5_hash") is None:
                        print("No MD5 Hash Supplied by Itch, assuming file is fine")
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
            else:
                print(f"File Already Exists! Skipping")
                return

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
        if self.verify:
            if itchiodl.utils.md5sum(f"{path}/{file}") != d.get("md5_hash"):
                if d.get("md5_hash") is None:
                    return
                print(f"Failed to verify {file}")
                return
                # Create checksum file
            if self.verify_file:
                with open(f"{path}/{file}.md5", "w") as f:
                    f.write(d["md5_hash"])

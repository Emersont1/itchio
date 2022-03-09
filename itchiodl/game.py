import re
import requests
import json
import os
import urllib


import itchiodl.utils


class Game:
    def __init__(self, data):
        self.data = data["game"]
        self.name = self.data["title"]
        self.publisher = self.data["user"]["username"]
        self.link = self.data["url"]

        self.id = data["id"]
        self.game_id = data["game_id"]

        matches = re.match(r"https://(.+)\.itch\.io/(.+)", self.link)
        self.game_slug = matches.group(2)
        self.publisher_slug = matches.group(1)

        self.files = []

    def load_downloads(self, token):
        self.downloads = []
        r = requests.get(
            f"https://api.itch.io/games/{self.game_id}/uploads?download_key_id={self.id}",
            headers={
                "Authorization": token})
        j = r.json()
        for d in j["uploads"]:
            self.downloads.append(d)

    def download(self, token):
        if os.path.exists(f"{self.publisher_slug}/{self.game_slug}.json"):
            print(f"Skipping Game {self.name}")
            return

        self.load_downloads(token)

        if not os.path.exists(self.publisher_slug):
            os.mkdir(self.publisher_slug)

        if not os.path.exists(f"{self.publisher_slug}/{self.game_slug}"):
            os.mkdir(f"{self.publisher_slug}/{self.game_slug}")

        for d in self.downloads:
            file = d['filename'] or d['display_name'] or d['id']
            path = f"{self.publisher_slug}/{self.game_slug}"
            if os.path.exists(f"{path}/{file}"):
                print(f"Skipping {path}/{file}")
                continue

            # Get UUID
            r = requests.post(
                f"https://api.itch.io/games/{self.game_id}/download-sessions",
                headers={
                    "Authorization": token})
            j = r.json()

            # Download
            url = f"https://api.itch.io/uploads/{d['id']}/download?api_key={token}&download_key_id={self.id}&uuid={j['uuid']}"
            # response_code = urllib.request.urlopen(url).getcode()
            try:
                itchiodl.utils.download(url, path, self.name + " - " + file)
            except itchiodl.utils.NoDownloadError as e:
                print("Http response is not a download, skipping")

                with open('errors.txt', 'a') as f:
                    f.write(f""" Cannot download game/asset: {self.game_slug}
                    Publisher Name: {self.publisher_slug}
                    Path: {path}
                    File: {file}
                    Request URL: {url}
                    This request failed due to a missing response header
                    This game/asset has been skipped please download manually
                    ---------------------------------------------------------\n """)

                continue
            except urllib.error.HTTPError as e:
                print("This one has broken due to an HTTP error!!")

                with open('errors.txt', 'a') as f:
                    f.write(f""" Cannot download game/asset: {self.game_slug}
                    Publisher Name: {self.publisher_slug}
                    Path: {path}
                    File: {file}
                    Request URL: {url}
                    Request Response Code: {e.code}
                    Error Reason: {e.reason}
                    This game/asset has been skipped please download manually
                    ---------------------------------------------------------\n """)

                continue

        with open(f"{self.publisher_slug}/{self.game_slug}.json", "w") as f:
            json.dump({
                "name": self.name,
                "publisher": self.publisher,
                "link": self.link,
                "itch_id": self.id,
                "game_id": self.game_id,
                "itch_data": self.data,
            }, f)

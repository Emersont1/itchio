import json
from concurrent.futures import ThreadPoolExecutor
import functools
import threading
import requests

from itchiodl.game import Game


class Library:
    """Representation of a user's game library"""

    def __init__(self, login, jobs=4):
        self.login = login
        self.games = []
        self.jobs = jobs

    def load_game_page(self, page):
        """Load a page of games via the API"""
        print("Loading page", page)
        r = requests.get(
            f"https://api.itch.io/profile/owned-keys?page={page}",
            headers={"Authorization": self.login},
        )
        j = json.loads(r.text)

        for s in j["owned_keys"]:
            self.games.append(Game(s))

        return len(j["owned_keys"])

    def load_games(self):
        """Load all games in the library via the API"""
        page = 1
        while True:
            n = self.load_game_page(page)
            if n == 0:
                break
            page += 1

    def download_library(self, platform=None):
        """Download all games in the library"""

        with ThreadPoolExecutor(max_workers=self.jobs) as executor:
            i = [0]
            l = len(self.games)
            lock = threading.RLock()

            def dl(i, g):
                x = g.download(self.login, platform)
                with lock:
                    i[0] += 1
                print(f"Downloaded {g.name} ({i[0]} of {l})")
                return x

            executor.map(functools.partial(dl, i), self.games)

import json
from concurrent.futures import ThreadPoolExecutor
import functools
import threading
import requests
from bs4 import BeautifulSoup

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

    def load_owned_games(self):
        """Load all games in the library via the API"""
        page = 1
        while True:
            n = self.load_game_page(page)
            if n == 0:
                break
            page += 1

    def load_game(self, publisher, title):
        """Load a game by publisher and title"""
        rsp = requests.get(
            f"https://{publisher}.itch.io/{title}/data.json",
            headers={"Authorization": self.login},
        )
        j = json.loads(rsp.text)
        game_id = j["id"]
        gsp = requests.get(
            f"https://api.itch.io/games/{game_id}/uploads",
            headers={"Authorization": self.login},
        )
        k = gsp.json()
        if k != {"uploads": {}}:
            self.games.append(Game(k))
            return
        print(f"{title} is a purchased game.")
        i = 1
        while self.games == []:
            j = self.load_game_page(i)

            self.games = [
                x
                for x in self.games
                if x.link == f"https://{publisher}.itch.io/{title}"
            ]

            if j == 0:
                break
            i += 1

        if self.games == []:
            print(f"Cannot find {title} in owned keys, you may not own it.")

    def load_games(self, publisher):
        """Load all games by publisher"""
        rsp = requests.get(f"https://{publisher}.itch.io")
        soup = BeautifulSoup(rsp.text, "html.parser")
        for link in soup.select("a.game_link"):
            game_id = link.get("data-label").split(":")[1]
            gsp = requests.get(
                f"https://api.itch.io/games/{game_id}",
                headers={"Authorization": self.login},
            )
            k = json.loads(gsp.text)
            self.games.append(Game(k))

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

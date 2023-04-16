from concurrent.futures import ThreadPoolExecutor
import functools
import threading
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from itchiodl.game import Game
from itchiodl.utils import NoDownloadError


class Library:
    """Representation of a user's game library"""

    def __init__(self, login, jobs=4):
        self.login = login
        self.games = []
        self.jobs = jobs
        self.key_pairs = {}

    def load_game_page(self, page):
        """Load a page of games via the API"""
        print("Loading page", page)
        r = requests.get(
            f"https://api.itch.io/profile/owned-keys?page={page}",
            headers={"Authorization": self.login},
        )
        j = r.json()

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

    def load_game_page_keys(self, page):
        """Load a page of game keys via the API"""
        duplicates = 0
        print("Loading page", page)
        r = requests.get(
            f"https://api.itch.io/profile/owned-keys?page={page}",
            headers={"Authorization": self.login},
        )
        j = json.loads(r.text)

        for s in j["owned_keys"]:
            if str(s.get("game_id")) in self.key_pairs:
                duplicates += 1
                # The duplicate download key check assumes that a consecutive
                # string of ten identical game ids indicates the list has not changed
                # Duplicate game keys can happen
                # if you buy multiple bundles containing the same item
                # print("duplicate game ID", s["game_id"]) # Old debug line
                if duplicates > 9:
                    print("Assuming that the owned keys have not changed")
                    return 0
            else:
                self.key_pairs.update({str(s["game_id"]): s["id"]})
                duplicates = 0

        return len(j["owned_keys"])

    def load_owned_keys(self):
        """Load game_id:download_id pairs only and stores them in the library.keyPairs dictionary"""
        page = 1
        p = Path("key_pairs.json")
        if p.exists():
            with p.open(mode="r") as infile:
                self.key_pairs.update(json.load(infile))
                infile.close()
        while True:
            n = self.load_game_page_keys(page)
            if n == 0:
                break
            page += 1
        with p.open(mode="w") as outfile:
            json.dump(self.key_pairs, outfile, indent=0)
            outfile.close()

    def load_game(self, publisher, title):
        """Load a game by publisher and title"""
        self.load_owned_keys()
        rsp = requests.get(
            f"https://{publisher}.itch.io/{title}/data.json",
            headers={"Authorization": self.login},
        )
        j = rsp.json()
        game_id = j["id"]
        gsp = requests.get(
            f"https://api.itch.io/games/{game_id}",
            headers={"Authorization": self.login},
        )
        k = json.loads(gsp.text)
        game = Game(k)
        if str(game_id) in self.key_pairs:
            game.id = self.key_pairs[str(game_id)]
        else:
            game.id = False
        game.game_id = game_id
        self.games.append(game)

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
            k = gsp.json()
            self.games.append(Game(k))

    def download_library(self, platform=None):
        """Download all games in the library"""
        with ThreadPoolExecutor(max_workers=self.jobs) as executor:
            i = [0, 0]
            ln = len(self.games)
            lock = threading.RLock()

            def dl(ix, g):
                try:
                    g.download(self.login, platform)
                    with lock:
                        i[0] += 1
                    print(f"Downloaded {g.name} ({ix[0]} of {ln})")
                except NoDownloadError as e:
                    print(e)
                    i[1] += 1

            r = executor.map(functools.partial(dl, i), self.games)
            for _ in r:
                pass
            print(f"Downloaded {i[0]} Games, {i[1]} Errors")

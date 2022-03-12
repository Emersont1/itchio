import requests
import json

from itchiodl.game import Game


class Library:
    def __init__(self, login):
        self.login = login
        self.games = []

    def load_game_page(self, page):
        print("Loading page", page)
        r = requests.get(
            f"https://api.itch.io/profile/owned-keys?page={page}",
            headers={
                "Authorization": self.login})
        j = json.loads(r.text)

        for s in j["owned_keys"]:
            self.games.append(Game(s))

        return len(j["owned_keys"])

    def load_games(self):
        page = 1
        while True:
            n = self.load_game_page(page)
            if n == 0:
                break
            page += 1

    def download_library(self):
        for game in self.games:
            game.download(self.login)

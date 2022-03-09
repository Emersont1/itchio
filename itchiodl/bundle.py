import requests
from bs4 import BeautifulSoup as soup


class Bundle:
    def __init__(self, login, url):
        self.login = login
        self.url = url

    def load_games(self):
        i = 1

        r = self.login.get(self.url)
        s = soup(r.text, "html.parser")
        pages = int(s.select("span.pager_label a")[-1].text)
        while i < pages:
            if self.load_game(i):
                i += 1
                print(f"Processing Page {i} of {pages}")

    def load_game(self, i):
        # Load 1 game. This will refresh the game afterwards, as the csrf token
        # will update
        r = self.login.get(f"{self.url}?page={i}")
        s = soup(r.text, "html.parser")
        for g in s.select("div.game_row"):
            name = g.select("h2 a")[0].text
            if f := g.find("form"):
                print(f"Processing {name}")

                game_id = f.find("input", {"name": "game_id"})["value"]
                csrf_token = f.find("input", {"name": "csrf_token"})["value"]

                data = {
                    "action": "claim",
                    "game_id": game_id,
                    "csrf_token": csrf_token}

                r = self.login.post(f"{self.url}?page={i}", data=data)
                return False
            # else:
            #    print(f"Skipping {name} - Already in Library")
        return True

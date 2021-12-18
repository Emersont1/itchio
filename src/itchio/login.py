import requests
import json
from bs4 import BeautifulSoup as soup
import requests

def LoginWeb(user, password):
        session = requests.Session()
        
        # GET the page first so we have a valid CSRF token value
        login1 = session.get("https://itch.io/login")
        s =  soup(login1.text, "html.parser")
        csrf_token = s.find("input", {"name": "csrf_token"})["value"]
        
        # Now POST the login
        r = session.post("https://itch.io/login", {"username": user, "password":password, "csrf_token": csrf_token})

        if r.status_code != 200:
            raise RuntimeError

        return session

def LoginAPI(user, password):
    r = requests.post("https://api.itch.io/login", {"username": user, "password":password, "source": "desktop"})
    if r.status_code != 200:
        raise RuntimeError
    t = json.loads(r.text)
    
    if not t["success"]:
        raise RuntimeError
    
    return t["key"]["key"]
    
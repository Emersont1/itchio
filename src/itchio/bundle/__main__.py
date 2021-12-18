from getpass import getpass
import itchio

user = input("Username: ")
password = getpass("Password: ")
 
l = itchio.LoginWeb(user, password)

url = input("Bundle URL: ")
b = itchio.Bundle(l, url)
b.load_games()
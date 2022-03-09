from getpass import getpass
import itchiodl

user = input("Username: ")
password = getpass("Password: ")
 
l = itchiodl.LoginWeb(user, password)

url = input("Bundle URL: ")
b = itchiodl.Bundle(l, url)
b.load_games()
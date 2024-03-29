from getpass import getpass
import itchiodl


def main():
    """CLI tool to at all games in a bundle to your library."""

    user = input("Username: ")
    password = getpass("Password: ")

    l = itchiodl.LoginWeb(user, password)

    url = input("Bundle URL: ")
    b = itchiodl.Bundle(l, url)
    b.load_games()


if __name__ == "__main__":
    main()

import argparse
from getpass import getpass

import itchiodl


def main():
    parser = argparse.ArgumentParser(
        prog='python -m hstp',
        description='Build an '
    )

    parser.add_argument(
        "-k",
        "--api-key",
        help="Use API key instead of username/password")

    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=4,
        help="Number of concurrent downloads, defaults to 4")

    args = parser.parse_args()

    l = ""

    if not args.api_key:
        user = input("Username: ")
        password = getpass("Password: ")
        l = itchiodl.LoginAPI(user, password)
    else:
        l = args.api_key

    lib = itchiodl.Library(l)
    lib.load_games()
    lib.download_library()


if __name__ == "__main__":
    main()

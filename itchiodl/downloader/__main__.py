import argparse
from getpass import getpass
import re

import itchiodl


def main():
    parser = argparse.ArgumentParser(prog="python -m hstp", description="Build an ")

    parser.add_argument(
        "-k", "--api-key", help="Use API key instead of username/password"
    )

    parser.add_argument(
        "-p",
        "--platform",
        help="Platform to download for (default: all), will accept values like 'windows', 'linux', 'osx' and android",
    )

    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=4,
        help="Number of concurrent downloads, defaults to 4",
    )

    parser.add_argument(
        "--download-publisher",
        type=str,
        help="Download all games from a specific publisher",
    )

    parser.add_argument(
        "--download-game",
        type=str,
        help="Download a specific game, should be in the format publisher.itch.io/game",
    )

    args = parser.parse_args()

    l = ""

    if not args.api_key:
        user = input("Username: ")
        password = getpass("Password: ")
        l = itchiodl.LoginAPI(user, password)
    else:
        l = args.api_key

    lib = itchiodl.Library(l, args.jobs)

    if args.download_publisher:
        lib.load_games(args.download_publisher)
    elif args.download_game:
        matches = re.match(r"https://(.+)\.itch\.io/(.+)", args.download_game)
        lib.load_game(matches.group(1), matches.group(2))
    else:
        lib.load_owned_games()

    lib.download_library(args.platform)


if __name__ == "__main__":
    main()

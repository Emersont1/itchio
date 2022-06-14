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
        "-vf",
        "--verbose-folders",
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help="Download Folders are named based on the full text version of the title instead of the trimmed URL title"
    )

    parser.add_argument(
        "--no-verify",
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help="Disables file verification entirely, files with the same name are assumed to be the same file"
    )

    parser.add_argument(
        "--no-verify-file",
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help="Disables writing md5 hashes to a supplementary file, does nothing if --no-verify is specified"
    )

    parser.add_argument(
        "-sas",
        "--skip-above-size",
        type=float,
        default=float('inf'),
        help="Skips individual files that are above the specified size threshold, size in MB, supports decimals"
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
        help="Download a specific game, should be in the format 'https://%publisher%.itch.io/%game-title%'",
    )

    parser.add_argument(
        "--skip-library-load",
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help="For the --download-game argument only, skips caching and checking the user library for an existing key"
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
        if not args.skip_library_load:
            lib.load_owned_games()
            for game in lib.games:
                if game.link == args.download_game:
                    lib.games = [game]
                    break
            if len(lib) > 1:
                print("Game Is Not In Library, Checking for Free Downloads")
                lib.games = []
                matches = re.match(r"https://(.+)\.itch\.io/(.+)", args.download_game)
                lib.load_game(matches.group(1), matches.group(2))
        else:
            matches = re.match(r"https://(.+)\.itch\.io/(.+)", args.download_game)
            lib.load_game(matches.group(1), matches.group(2))
    else:
        lib.load_owned_games()

    lib.download_library(args.platform)


if __name__ == "__main__":
    main()

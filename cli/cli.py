import os
import logging
import argparse

import naz


def main():
    """
    """
    # TODO: enable people to specify the location where they want certificate and keys to be stored.
    # currently, we store them in the directory from which sewer is ran
    parser = argparse.ArgumentParser(
        prog="naz",
        description="""naz is an SMPP client.
            naz-cli \
            """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version="67"),
        help="The currently installed naz version.",
    )

    args = parser.parse_args()


main()

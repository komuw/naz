import os
import logging
import argparse

import naz


def main():
    """
    """
    parser = argparse.ArgumentParser(
        prog="naz",
        description="""naz is an SMPP client.
            naz-cli \
            """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=naz.__version__.about["__version__"]),
        help="The currently installed naz version.",
    )

    args = parser.parse_args()


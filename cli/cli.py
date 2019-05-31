import os
import sys
import random
import string
import asyncio
import logging
import inspect
import argparse

import naz

from .utils import sig, load

os.environ["PYTHONASYNCIODEBUG"] = "1"


def load_class(dotted_path):
    """
    taken from: https://github.com/coleifer/huey/blob/4138d454cc6fd4d252c9350dbd88d74dd3c67dcb/huey/utils.py#L44
    huey is released under MIT license a copy of which can be found at: https://github.com/coleifer/huey/blob/master/LICENSE

    The license is also included below:

    Copyright (c) 2017 Charles Leifer

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
    """
    try:
        path, klass = dotted_path.rsplit(".", 1)
        __import__(path)
        mod = sys.modules[path]
        attttr = getattr(mod, klass)
        return attttr
    except Exception:
        cur_dir = os.getcwd()
        if cur_dir not in sys.path:
            sys.path.insert(0, cur_dir)
            return load_class(dotted_path)
        err_mesage = "Error importing {0}".format(dotted_path)
        sys.stderr.write("\033[91m{0}\033[0m\n".format(err_mesage))
        raise


def make_parser():
    """
    this is abstracted into its own method so that it is easier to test it.
    """
    parser = argparse.ArgumentParser(
        prog="naz",
        description="""naz is an async SMPP client.
                example usage:
                naz-cli \
                --client dotted.path.to.naz.Client.instance
                """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=naz.__version__.about["__version__"]),
        help="The currently installed naz version.",
    )
    parser.add_argument(
        "--client",
        required=True,
        help="The dotted path to a python file conatining a `naz.Client` instance. \
        eg: --client dotted.path.to.a.naz.Client.class.instance",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        required=False,
        default=False,
        help="""Whether we want to do a dry-run of the naz cli.
        This is typically only used by developers who are developing naz.
        eg: --dry-run""",
    )
    return parser


def main():
    """
    """
    _client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=17))
    logger = naz.logger.SimpleLogger("naz.cli")
    logger.log(logging.INFO, "\n\n\t {} \n\n".format("Naz: the SMPP client."))
    logger.log(logging.INFO, {"event": "naz.cli.main", "stage": "start", "client_id": _client_id})

    loop = asyncio.get_event_loop()
    try:
        parser = make_parser()
        args = parser.parse_args()
        dry_run = args.dry_run
        client = args.client
        client = load.load_class(dotted_path=client, logger=logger)
        if dry_run:
            logger.log(
                logging.WARN,
                "\n\n\t {} \n\n".format(
                    "Naz: Caution; You have activated dry-run, naz may not behave correctly."
                ),
            )

        if not isinstance(client, naz.Client):
            err = ValueError(
                """`client` should be of type:: `naz.Client` You entered: {0}""".format(
                    type(client)
                )
            )
            logger.log(logging.ERROR, {"event": "naz.cli.main", "stage": "end", "error": str(err)})
            sys.exit(77)

        if dry_run:
            return
        # call naz api
        loop.run_until_complete(
            async_main(client=client, logger=logger, loop=loop, dry_run=dry_run)
        )
    except Exception as e:
        logger.log(logging.ERROR, {"event": "naz.cli.main", "stage": "end", "error": str(e)})
        sys.exit(77)
    finally:
        logger.log(logging.INFO, {"event": "naz.cli.main", "stage": "end"})


async def async_main(
    client: naz.Client,
    logger: naz.logger.SimpleLogger,
    loop: asyncio.events.AbstractEventLoop,
    dry_run: bool,
):
    # connect & bind to the SMSC host
    await client.connect()
    await client.tranceiver_bind()

    # send any queued messages to SMSC, read any data from SMSC and continually check the state of the SMSC
    tasks = asyncio.gather(
        client.dequeue_messages(TESTING=dry_run),
        client.receive_data(TESTING=dry_run),
        client.enquire_link(TESTING=dry_run),
        sig._signal_handling(logger=logger, client=client, loop=loop),
        loop=loop,
    )
    await tasks


if __name__ == "__main__":
    main()

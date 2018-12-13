import os
import sys
import json
import random
import string
import asyncio
import logging
import inspect
import argparse

import naz

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
        description="""naz is an SMPP client.
                example usage:
                naz-cli \
                --config /path/to/my_config.json
                """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=naz.__version__.about["__version__"]),
        help="The currently installed naz version.",
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        required=False,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="The log level to output log messages at. \
        eg: --loglevel DEBUG",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=argparse.FileType(mode="r"),
        help="The config file to use. \
        eg: --config /path/to/my_config.json",
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
    logger = logging.getLogger("naz.cli")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel("DEBUG")
    logger.info({"event": "naz.cli.main", "stage": "start"})

    loop = asyncio.get_event_loop()
    try:
        parser = make_parser()
        args = parser.parse_args()

        dry_run = args.dry_run
        config = args.config
        config_contents = config.read()
        # todo: validate that config_contents hold all the required params
        kwargs = json.loads(config_contents)

        loglevel = (
            kwargs.get("loglevel").upper() if kwargs.get("loglevel") else args.loglevel.upper()
        )
        logger.setLevel(loglevel)
        log_metadata = kwargs.get("log_metadata")
        if not log_metadata:
            log_metadata = {}
        client_id = kwargs.get("client_id")
        if not client_id:
            client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=17))
            kwargs["client_id"] = client_id
        log_metadata.update(
            {
                "smsc_host": kwargs.get("smsc_host"),
                "system_id": kwargs.get("system_id"),
                "client_id": client_id,
            }
        )
        extra_log_data = {"log_metadata": log_metadata}
        logger = naz.client.NazLoggingAdapter(logger, extra_log_data)

        logger.info("\n\n\t {} \n\n".format("Naz: the SMPP client."))
        if dry_run:
            logger.warn(
                "\n\n\t {} \n\n".format(
                    "Naz: Caution; You have activated dry-run, naz may not behave correctly."
                )
            )

        # Load custom classes
        # Users can ONLY pass in:
        # 1. python class instances
        # if the thing that the user passed in is a python class, we need to exit with an error
        # we'll use `inspect.isclass` to do that
        # todo: test the h** out of this logic

        outboundqueue = load_class(kwargs["outboundqueue"])  # this is a mandatory param
        kwargs["outboundqueue"] = outboundqueue
        if inspect.isclass(outboundqueue):
            # DO NOT instantiate class instance, fail with appropriate error instead.
            msg = "outboundqueue should be a class instance."
            logger.exception({"event": "naz.cli.main", "stage": "end", "error": msg})
            sys.exit(77)

        sequence_generator = kwargs.get("sequence_generator")
        if sequence_generator:
            sequence_generator = load_class(sequence_generator)
            # kwargs should contain the actual loaded class instances
            kwargs["sequence_generator"] = sequence_generator
            if inspect.isclass(sequence_generator):
                msg = "sequence_generator should be a class instance."
                logger.exception({"event": "naz.cli.main", "stage": "end", "error": msg})
                sys.exit(77)

        codec_class = kwargs.get("codec_class")
        if codec_class:
            codec_class = load_class(codec_class)
            kwargs["codec_class"] = codec_class
            if inspect.isclass(codec_class):
                msg = "codec_class should be a class instance."
                logger.exception({"event": "naz.cli.main", "stage": "end", "error": msg})
                sys.exit(77)
        rateLimiter = kwargs.get("rateLimiter")
        if rateLimiter:
            rateLimiter = load_class(rateLimiter)
            kwargs["rateLimiter"] = rateLimiter
            if inspect.isclass(rateLimiter):
                msg = "rateLimiter should be a class instance."
                logger.exception({"event": "naz.cli.main", "stage": "end", "error": msg})
                sys.exit(77)
        hook = kwargs.get("hook")
        if hook:
            hook = load_class(hook)
            kwargs["hook"] = hook
            if inspect.isclass(hook):
                msg = "hook should be a class instance."
                logger.exception({"event": "naz.cli.main", "stage": "end", "error": msg})
                sys.exit(77)
        throttle_handler = kwargs.get("throttle_handler")
        if throttle_handler:
            throttle_handler = load_class(throttle_handler)
            kwargs["throttle_handler"] = throttle_handler
            if inspect.isclass(throttle_handler):
                msg = "throttle_handler should be a class instance."
                logger.exception({"event": "naz.cli.main", "stage": "end", "error": msg})
                sys.exit(77)

        if dry_run:
            return

        # call naz api
        cli = naz.Client(async_loop=loop, **kwargs)
        # connect to the SMSC host
        reader, writer = loop.run_until_complete(cli.connect())
        # bind to SMSC as a tranceiver
        loop.run_until_complete(cli.tranceiver_bind())

        # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
        tasks = asyncio.gather(
            cli.send_forever(TESTING=dry_run),
            cli.receive_data(TESTING=dry_run),
            cli.enquire_link(TESTING=dry_run),
        )
        loop.run_until_complete(tasks)
        loop.run_until_complete(cli.unbind())
    except Exception as e:
        logger.exception({"event": "naz.cli.main", "stage": "end", "error": str(e)})
        sys.exit(77)
    finally:
        logger.info({"event": "naz.cli.main", "stage": "end"})


if __name__ == "__main__":
    main()

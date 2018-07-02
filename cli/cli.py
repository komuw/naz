import os
import sys
import json
import asyncio
import logging
import inspect
import argparse

import naz


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


def main():
    """
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

    args = parser.parse_args()

    config = args.config
    config_contents = config.read()
    kwargs = json.loads(config_contents)
    # todo: validate that config_contents hold all the required params
    loglevel = kwargs.get("loglevel").upper() if kwargs.get("loglevel") else args.loglevel.upper()

    log_metadata = kwargs.get("log_metadata")
    if not log_metadata:
        log_metadata = {}
    log_metadata.update(
        {"smsc_host": kwargs.get("smsc_host"), "system_id": kwargs.get("system_id")}
    )

    extra_log_data = {"log_metadata": log_metadata}
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s. log_metadata=%(log_metadata)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(loglevel)
    logger = logging.LoggerAdapter(logger, extra_log_data)

    logger.info("\n\n\t Naz: the SMPP client. \n\n")

    # Load custom classes #######################
    # Users can either pass in:
    # 1. python classes;
    # 2. python class instances
    # if the thing that the user passed in is a python class, we need to create a class instance.
    # we'll use `inspect.isclass` to do that
    # todo: test the h** out of this logic

    outboundqueue = load_class(kwargs["outboundqueue"])  # this is a mandatory param
    if inspect.isclass(outboundqueue):
        # instantiate class instance
        outboundqueue = outboundqueue()
    kwargs["outboundqueue"] = outboundqueue

    sequence_generator = kwargs.get("sequence_generator")
    if sequence_generator:
        sequence_generator = load_class(sequence_generator)
        if inspect.isclass(sequence_generator):
            # instantiate an object
            kwargs["sequence_generator"] = sequence_generator()

    codec_class = kwargs.get("codec_class")
    if codec_class:
        codec_class = load_class(codec_class)
        if inspect.isclass(codec_class):
            kwargs["codec_class"] = codec_class()
    rateLimiter = kwargs.get("rateLimiter")
    if rateLimiter:
        rateLimiter = load_class(rateLimiter)
        if inspect.isclass(rateLimiter):
            kwargs["rateLimiter"] = rateLimiter()
    hook = kwargs.get("hook")
    if hook:
        hook = load_class(hook)
        if inspect.isclass(hook):
            kwargs["hook"] = hook()
    # Load custom classes #######################

    # call naz api ###########
    loop = asyncio.get_event_loop()
    cli = naz.Client(async_loop=loop, **kwargs)
    # queue messages to send
    for i in range(0, 20):
        item_to_enqueue = {
            "event": "submit_sm",
            "short_message": "Hello World-{0}".format(str(i)),
            "correlation_id": "myid12345",
            "source_addr": "254722111111",
            "destination_addr": "254722999999",
        }
        loop.run_until_complete(kwargs["outboundqueue"].enqueue(item_to_enqueue))

    # connect to the SMSC host
    reader, writer = loop.run_until_complete(cli.connect())
    # bind to SMSC as a tranceiver
    loop.run_until_complete(cli.tranceiver_bind())

    try:
        # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
        gathering = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
        loop.run_until_complete(gathering)
        loop.run_forever()
    except Exception as e:
        logger.exception("exception occured. error={0}".format(str(e)))
        pass
    finally:
        loop.run_until_complete(cli.unbind())
        loop.close()
    # call naz api ###########


# todo: remove this after testing
main()

import sys
import json
import asyncio
import logging
import argparse

import naz


def load_class(dotted_path):
    """
    taken from: https://github.com/coleifer/huey/blob/4138d454cc6fd4d252c9350dbd88d74dd3c67dcb/huey/utils.py#L44
    huey is released under MIT license a copy of which can be found at: https://github.com/coleifer/huey/blob/master/LICENSE
    """
    path, klass = dotted_path.rsplit(".", 1)
    __import__(path)
    mod = sys.modules[path]
    attttr = getattr(mod, klass)
    return attttr


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
    loglevel = args.loglevel
    config = args.config
    config_contents = config.read()
    kwargs = json.loads(config_contents)
    # todo: validate that config_contents hold all the required params

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
    logger.setLevel(loglevel.upper())
    logger = logging.LoggerAdapter(logger, extra_log_data)

    logger.info("\n\n\t Naz: the SMPP client. \n\n")

    # Load custom classes #######################
    sequence_generator = kwargs.get("sequence_generator")
    if sequence_generator:
        kwargs["sequence_generator"] = load_class(sequence_generator)
    outboundqueue = kwargs.get("outboundqueue")
    if outboundqueue:
        kwargs["outboundqueue"] = load_class(outboundqueue)
    codec_class = kwargs.get("codec_class")
    if codec_class:
        kwargs["codec_class"] = load_class(codec_class)
    rateLimiter = kwargs.get("rateLimiter")
    if rateLimiter:
        kwargs["rateLimiter"] = load_class(rateLimiter)
    hook = kwargs.get("hook")
    if hook:
        kwargs["hook"] = load_class(hook)
    # Load custom classes #######################

    # call naz api ###########
    loop = asyncio.get_event_loop()
    cli = naz.Client(async_loop=loop, **kwargs)
    # queue messages to send
    for i in range(0, 20):
        loop.run_until_complete(
            cli.submit_sm(
                msg="Hello World-{0}.".format(str(i)),
                correlation_id="myid12345",
                source_addr="254722111111",
                destination_addr="254722999999",
            )
        )

    # connect to the SMSC host
    reader, writer = loop.run_until_complete(cli.connect())
    # bind to SMSC as a tranceiver
    loop.run_until_complete(cli.tranceiver_bind())

    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    gathering = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(gathering)

    loop.run_forever()
    loop.close()
    # call naz api ###########


# todo: remove this after testing
main()

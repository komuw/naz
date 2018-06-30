import json
import argparse
import asyncio

import naz


def main():
    """
    """
    parser = argparse.ArgumentParser(
        prog="naz",
        description="""naz is an SMPP client.
            naz-cli \
            --config /path/to/config.json
            """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=naz.__version__.about["__version__"]),
        help="The currently installed naz version.",
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

    # call naz api ###########
    loop = asyncio.get_event_loop()
    cli = naz.Client(async_loop=loop, **kwargs)
    # queue messages to send
    for i in range(0, 4):
        print("submit_sm round:", i)
        loop.run_until_complete(
            cli.submit_sm(
                msg="Hello World-{0}".format(str(i)),
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


# todo remove this call here
main()

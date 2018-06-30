import os
import logging
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
            """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=naz.__version__.about["__version__"]),
        help="The currently installed naz version.",
    )

    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["run", "something"],
        help="The action that you want to perform. \
        Either run (example app) or something (do something). \
        eg: --action run",
    )

    args = parser.parse_args()

    action = args.action
    if action == "run":
        loop = asyncio.get_event_loop()
        # todo: instantiate client with args that we got from user supplied command line args
        cli = naz.Client(
            async_loop=loop,
            SMSC_HOST="127.0.0.1",
            SMSC_PORT=2775,
            system_id="smppclient1",
            password="password",
        )
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

    else:
        print("nothing to do.")


# todo remove this call here
main()

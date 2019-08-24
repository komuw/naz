import sys
import random
import string
import asyncio
import logging

import naz

from app import my_naz_client, country_code


async def send_messages():
    """
    - generate a random message of between 1-254 bytes.
    - generate a random msisdn
    - send the message
    """
    source_addr = "NazBenchmarksInc"
    # DURATION_BETWEEN_MSGS = 0.05
    MAX_NUM_OF_MESSAGES = 100_004
    MSGS_SENT = 0

    logger = naz.log.SimpleLogger("naz_benchmarks.message_producer")
    while True:
        try:
            log_id = "{}-".format(MSGS_SENT + 1) + "".join(
                random.choices(string.ascii_lowercase, k=7)
            )
            destination_addr = country_code + str(random.randint(100_000_000, 900_000_000))  # nosec
            msg_size = random.randint(  # nosec
                1, 200
            )  # an smpp msg should be between 0-254 octets(bytes)
            msg = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=msg_size)  # nosec
            )
            if sys.getsizeof(msg) > 250:
                e = ValueError("message size too big")
                logger.log(
                    logging.ERROR,
                    {
                        "event": "message_producer.send",
                        "stage": "start",
                        "destination_addr": destination_addr,
                        "log_id": log_id,
                        "msg": msg[:10],
                        "error": str(e),
                        "MSGS_SENT": MSGS_SENT,
                    },
                )
                raise e
            if len(source_addr) > 20:  # source_addr should be max of 21 octets/bytes
                e = ValueError("source_addr size too big")
                logger.log(
                    logging.ERROR,
                    {
                        "event": "message_producer.send",
                        "stage": "start",
                        "destination_addr": destination_addr,
                        "log_id": log_id,
                        "msg": msg[:10],
                        "error": str(e),
                        "MSGS_SENT": MSGS_SENT,
                    },
                )
                raise e
            if len(destination_addr) > 20:  # destination_addr should be max of 21 octets/bytes
                e = ValueError("destination_addr size too big")
                logger.log(
                    logging.ERROR,
                    {
                        "event": "message_producer.send",
                        "stage": "start",
                        "destination_addr": destination_addr,
                        "log_id": log_id,
                        "msg": msg[:10],
                        "error": str(e),
                        "MSGS_SENT": MSGS_SENT,
                    },
                )
                raise e

            logger.log(
                logging.INFO,
                {
                    "event": "message_producer.send",
                    "stage": "start",
                    "destination_addr": destination_addr,
                    "log_id": log_id,
                    "msg": msg,
                    "MSGS_SENT": MSGS_SENT,
                },
            )
            await my_naz_client.submit_sm(
                short_message=msg,
                log_id=log_id,
                source_addr=source_addr,
                destination_addr=destination_addr,
            )
            logger.log(
                logging.INFO,
                {
                    "event": "message_producer.send",
                    "stage": "end",
                    "destination_addr": destination_addr,
                    "log_id": log_id,
                    "msg": msg,
                    "MSGS_SENT": MSGS_SENT,
                },
            )
            MSGS_SENT = MSGS_SENT + 1
            if MSGS_SENT == MAX_NUM_OF_MESSAGES:
                logger.log(
                    logging.INFO,
                    {
                        "event": "message_producer.send",
                        "stage": "end",
                        "state": "ALL MESSAGES SENT SUCCESSFULLY",
                        "MSGS_SENT": MSGS_SENT,
                    },
                )
                sys.exit(0)
            # await asyncio.sleep(DURATION_BETWEEN_MSGS)
        except Exception as e:
            logger.log(
                logging.ERROR,
                {
                    "event": "message_producer.send",
                    "stage": "end",
                    "error": str(e),
                    "MSGS_SENT": MSGS_SENT,
                },
            )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_messages())

import sys
import random
import string
import asyncio
import logging

import naz

from app import my_naz_client

DURATION_BETWEEN_MSGS = 0.05
MAX_NUM_OF_MESSAGES = 100_001


async def send_messages():
    """
    - generate a random message of between 1-254 bytes.
    - generate a random msisdn
    - send the message
    """
    logger = naz.logger.SimpleLogger("naz_benchmarks.message_producer")

    country_code = "254"
    source_addr = "NazBenchmarksInc"

    for i in range(0, MAX_NUM_OF_MESSAGES):
        log_id = "{}-".format(i) + "".join(random.choices(string.ascii_lowercase, k=7))
        destination_addr = country_code + str(random.randint(100_000_000, 900_000_000))
        msg_size = random.randint(1, 200)  # an smpp msg should be between 0-254 octets(bytes)
        msg = "".join(random.choices(string.ascii_uppercase + string.digits, k=msg_size))
        if sys.getsizeof(msg) > 250:
            err = ValueError("message size too big")
            logger.log(
                logging.ERROR,
                {
                    "event": "message_producer.send",
                    "stage": "start",
                    "destination_addr": destination_addr,
                    "log_id": log_id,
                    "msg": msg[:10],
                    "error": str(err),
                },
            )
            raise err
        if len(source_addr) > 20:  # source_addr should be max of 21 octets/bytes
            err = ValueError("source_addr size too big")
            logger.log(
                logging.ERROR,
                {
                    "event": "message_producer.send",
                    "stage": "start",
                    "destination_addr": destination_addr,
                    "log_id": log_id,
                    "msg": msg[:10],
                    "error": str(err),
                },
            )
            raise err
        if len(destination_addr) > 20:  # destination_addr should be max of 21 octets/bytes
            err = ValueError("destination_addr size too big")
            logger.log(
                logging.ERROR,
                {
                    "event": "message_producer.send",
                    "stage": "start",
                    "destination_addr": destination_addr,
                    "log_id": log_id,
                    "msg": msg[:10],
                    "error": str(err),
                },
            )
            raise err

        logger.log(
            logging.INFO,
            {
                "event": "message_producer.send",
                "stage": "start",
                "destination_addr": destination_addr,
                "log_id": log_id,
                "msg": msg,
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
            },
        )
        # await asyncio.sleep(DURATION_BETWEEN_MSGS)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_messages())

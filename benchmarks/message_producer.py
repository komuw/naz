import sys
import time
import random
import string
import asyncio
import logging

import naz

from app import my_naz_client

DURATION_BETWEEN_MSGS = 10


async def send_messages():
    """
    - generate a random message of between 1-254 bytes.
    - generate a random msisdn
    - send the message
    """
    logger = naz.logger.SimpleLogger("naz_benchmarks.message_producer")

    country_code = "254"

    while True:
        # for i in range(0, 3):
        log_id = "log_id"
        destination_phone_number = country_code + str(random.randint(100_000_000, 900_000_000))
        msg_size = random.randint(1, 150)  # an smpp msg should be between 0-254 octets(bytes)
        msg = "".join(random.choices(string.ascii_uppercase + string.digits, k=msg_size))
        if sys.getsizeof(msg) > 250:
            logger.log(
                logging.ERROR,
                {
                    "event": "message_producer.send",
                    "stage": "start",
                    "destination_phone_number": destination_phone_number,
                    "log_id": log_id,
                    "msg": msg[:10],
                    "error": "message size too big",
                },
            )
            continue

        logger.log(
            logging.INFO,
            {
                "event": "message_producer.send",
                "stage": "start",
                "destination_phone_number": destination_phone_number,
                "log_id": log_id,
                "msg": msg,
            },
        )
        await my_naz_client.submit_sm(
            short_message=msg,
            log_id=log_id,
            source_addr="Naz Benchmarks Corporation",
            destination_addr=destination_phone_number,
        )
        logger.log(
            logging.INFO,
            {
                "event": "message_producer.send",
                "stage": "end",
                "destination_phone_number": destination_phone_number,
                "log_id": log_id,
                "msg": msg,
            },
        )
        await asyncio.sleep(DURATION_BETWEEN_MSGS)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_messages())

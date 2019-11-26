import os
import json
import asyncio
import datetime
import logging

import naz
import asyncpg


logger = naz.log.SimpleLogger("naz_benchmarks.log_collector")
logger.log(logging.INFO, {"event": "log_collector.start"})


async def send_log_to_remote_storage(logs):
    """
    send the log data to postgres/timescaleDB so that it can be analysed later.

    A log record looks like:
      {
        "timestamp": "2019-06-05 09:13:58,720",
        "event": "naz.SimpleRateLimiter.limit",
        "stage": "start",
        "project": "naz_benchmarks",
        "smsc_host": "smsc_server",
        "system_id": "smppclient1",
        "client_id": "R3H5CSO5Y2DTZFOKB",
        "pid": 1,
        }
    we extract(by popping) the main items from it like, timestamp, event, log_id, error etc so that they can be saved as individual fields in a db.
    The remaining dict is saved as JSONB field in the deb.
    """
    timeout = 12.0
    try:
        host = "localhost"
        if os.environ.get("IN_DOCKER"):
            host = "timescale_db"
        conn = await asyncpg.connect(
            host=host,
            port=5432,
            user="myuser",
            password=os.environ["POSTGRES_PASSWORD"],
            database="mydb",
            timeout=timeout,
            command_timeout=timeout,
        )

        all_logs = []
        for i in logs:
            timestamp = datetime.datetime.now(
                tz=datetime.timezone.utc
            )  # ignore the log timestamp for now
            event = i.pop("event", "")
            stage = i.pop("stage", "")
            client_id = i.pop("client_id", "")
            log_id = i.pop("log_id", "")
            error = i.pop("error", "")

            metadata = json.dumps({})
            try:
                metadata = json.dumps(i)
            except (json.decoder.JSONDecodeError, TypeError):
                pass

            all_logs.append((timestamp, event, stage, client_id, log_id, error, metadata))

        # batch insert
        await conn.executemany(
            """
            INSERT INTO logs(timestamp, event, stage, client_id, log_id, error, metadata)
                      VALUES($1, $2, $3, $4, $5, $6, $7)
            """,
            all_logs,
            timeout=timeout,
        )

        await conn.close()
        logger.log(logging.INFO, {"event": "log_sender_insert.end", "GOT_ERROR": error})

    except Exception as e:
        logger.log(logging.ERROR, {"event": "log_sender_insert.error", "error": str(e)})


async def read_log_file():
    with open("/usr/src/nazLog/naz_log_file", "r+") as log_file:
        for line in log_file:
            logger.log(logging.INFO, {"event": "log_collector.data", "line": line})

            log = None
            try:
                log = json.loads(line)
            except (json.decoder.JSONDecodeError, TypeError):
                pass
            logger.log(logging.INFO, {"event": "log_collector.log", "log": log})
            if log:
                await send_log_to_remote_storage(logs=[log])

        # clear file
        log_file.truncate(0)


async def collect_logs():
    while True:
        try:
            logger.log(logging.INFO, {"event": "log_collector.read"})
            await read_log_file()
            await asyncio.sleep(7)
        except OSError as e:
            if e.errno == 6:
                pass
            else:
                logger.log(logging.ERROR, {"event": "log_collector.error", "error": str(e)})
            await asyncio.sleep(7)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(collect_logs(), loop=loop)
    loop.run_until_complete(tasks)

    loop.close()
    logger.log(logging.INFO, {"event": "log_collector.end"})

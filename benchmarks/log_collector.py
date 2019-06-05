import os
import json
import random
import asyncio
import datetime
import logging

import naz
import asyncpg


logger = naz.logger.SimpleLogger("naz_benchmarks.log_collector")
logger.log(logging.INFO, {"event": "log_collector.start"})


class Buffer:
    def __init__(self, interval=12):
        self.interval = interval

        self.lock = asyncio.Semaphore(value=1)  # asyncio.Lock()
        self.buf = []

    def send_logs_every(self):
        jitter = random.randint(1, 9) * 0.1
        return self.interval + jitter


bufferedLogs = Buffer()


async def collect_logs():
    while True:
        try:
            logger.log(logging.INFO, {"event": "log_collector.read"})
            with open("/tmp/nazLog/naz_log_file", "r+") as log_file:
                for line in log_file:
                    logger.log(logging.INFO, {"event": "log_collector.data", "line": line})
                    log = await handle_logs(log_event=line)
                    logger.log(logging.INFO, {"event": "log_collector.log", "log": log})

                    # do not buffer if there are no logs
                    if log:
                        # TODO: disable locks/batched log sending if we get
                        # 'got Future attached to a different loop' errors
                        async with bufferedLogs.lock:
                            bufferedLogs.buf.append(log)

                # clear file
                log_file.truncate(0)
                await asyncio.sleep(7)
        except OSError as e:
            if e.errno == 6:
                pass
            else:
                logger.log(logging.ERROR, {"event": "log_collector.error", "error": str(e)})
                pass
            await asyncio.sleep(7)


async def handle_logs(log_event):
    log = None
    try:
        log = json.loads(log_event)
    except json.decoder.JSONDecodeError:
        pass
    return log


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
    try:
        host = "localhost"
        if os.environ.get("IN_DOCKER"):
            host = "timescale_db"
        conn = await asyncpg.connect(
            host=host,
            port=5432,
            user="myuser",
            password="hey_NSA",
            database="mydb",
            timeout=6.0,
            command_timeout=8.0,
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
            except Exception:
                pass

            all_logs.append((timestamp, event, stage, client_id, log_id, error, metadata))

        # batch insert
        await conn.executemany(
            """
            INSERT INTO logs(timestamp, event, stage, client_id, log_id, error, metadata)
                      VALUES($1, $2, $3, $4, $5, $6, $7)
            """,
            all_logs,
            timeout=8.0,
        )

        await conn.close()
        logger.log(logging.INFO, {"event": "log_sender_insert.end", "GOT_ERROR": error})

    except Exception as e:
        logger.log(logging.ERROR, {"event": "log_sender_insert.error", "error": str(e)})


async def schedule_log_sending():
    while True:
        async with bufferedLogs.lock:
            buf = bufferedLogs.buf
            if len(buf) > 0:
                await send_log_to_remote_storage(logs=buf)
                bufferedLogs.buf = []

        await asyncio.sleep(bufferedLogs.send_logs_every())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(collect_logs(), schedule_log_sending(), loop=loop)
    loop.run_until_complete(tasks)

    loop.close()
    logger.log(logging.INFO, {"event": "log_collector.end"})

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


class PIPE:
    def __init__(self, mode, fifo_file_name="/tmp/namedPipes/naz_log_named_pipe"):
        self.mode = mode
        # NB: collector should not try to create named pipe
        # instead it should use the named pipe that was attached
        # to it by the log_emitter container
        self.fifo_file_name = fifo_file_name
        self.fifo_file = None

    def __enter__(self):
        self.fifo_file = open(self.fifo_file_name, mode=self.mode)
        os.set_blocking(self.fifo_file.fileno(), False)

        return self.fifo_file

    def __exit__(self, type, value, traceback):
        if self.fifo_file:
            self.fifo_file.close()

    async def __aenter__(self):
        self.fifo_file = open(self.fifo_file_name, mode=self.mode)
        os.set_blocking(self.fifo_file.fileno(), False)

        return await asyncio.sleep(-1, result=self.fifo_file)

    async def __aexit__(self, exc_type, exc, tb):
        if self.fifo_file:
            await asyncio.sleep(-1, result=self.fifo_file.close())


async def collect_logs():
    async with PIPE(mode="r") as f:
        while True:
            try:
                logger.log(logging.INFO, {"event": "log_collector.read"})
                data = f.readline()
                if len(data) == 0:
                    # End of the file
                    await asyncio.sleep(1)
                    continue

                logger.log(logging.INFO, {"event": "log_collector.data", "data": data})
                log = await handle_logs(log_event=data)

                # do not buffer if there are no logs
                if log:
                    # TODO: disable locks/batched log sending if we get
                    # 'got Future attached to a different loop' errors
                    async with bufferedLogs.lock:
                        bufferedLogs.buf.append(log)
            except OSError as e:
                if e.errno == 6:
                    pass
                else:
                    logger.log(logging.ERROR, {"event": "log_collector.error", "error": str(e)})

                    pass


async def handle_logs(log_event):
    log = None
    try:
        log = json.loads(log_event)
    except json.decoder.JSONDecodeError:
        pass
    return log


async def send_log_to_remote_storage(logs):
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
            time = datetime.datetime.strptime(i["time"], "%Y-%m-%d %H:%M:%S.%f%z")
            application_name = i["application_name"]
            application_version = i["application_version"]
            environment_name = i["environment_name"]
            log_event = i["log_event"]
            trace_id = i["trace_id"]
            file_path = i["file_path"]
            host_ip = i["host_ip"]
            data = i.get("data")
            if data:
                data = json.dumps(data)

            all_logs.append(
                (
                    time,
                    application_name,
                    application_version,
                    environment_name,
                    log_event,
                    trace_id,
                    file_path,
                    host_ip,
                    data,
                )
            )

        # batch insert
        await conn.executemany(
            """
            INSERT INTO logs(time, application_name, application_version, environment_name, log_event, trace_id, file_path, host_ip, data)
                      VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            all_logs,
            timeout=8.0,
        )

        await conn.close()
        logger.log(logging.INFO, {"event": "log_sender_insert.end"})

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

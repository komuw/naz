import os
import time
import random
import typing
import logging
import threading

import naz
import docker


class Server:
    """
    This is a container scheduler; or you can call it a poor man's kubernetes.

    It laucnhes SMSC server and redis servers.
    It keeps them running & stops them randomly so as to simulate fault; you can call it a poor man's chaos monkey.
    """

    def __init__(
        self,
        image_name: str,
        container_name: str,
        labels: dict,
        ports: dict,
        command: typing.Union[None, str] = None,
        chaos: bool = True,
    ) -> None:
        self.image_name = image_name
        self.container_name = container_name
        self.labels = labels
        self.ports = ports
        self.command = command
        self.chaos = chaos

        self.docker_client = docker.from_env()
        self.logger = naz.log.SimpleLogger("naz_benchmarks.{0}".format(self.container_name))
        self.logger.bind(
            level="INFO", log_metadata={"container_name": self.container_name, "chaos": self.chaos}
        )

        self.container_max_run_duration: float = 16.00  # mins
        self.container_min_run_duration: float = 13.00  # mins

        self.container_max_stop_duration: float = 3.00  # mins
        self.container_min_stop_duration: float = 1.00  # mins

    def start(self):
        self.stop()
        self.docker_client.containers.run(
            self.image_name,
            command=self.command,
            name=self.container_name,
            detach=True,
            auto_remove=True,
            labels=self.labels,
            ports=self.ports,
            stdout=True,
            stderr=True,
        )

    def stop(self):
        try:
            running_containers = self.docker_client.containers.list()
            for container in running_containers:
                if container.name == self.container_name:
                    container.stop()
        except Exception as e:
            self.logger.log(
                logging.DEBUG, {"event": "Server.stop", "stage": "end", "error": str(e)}
            )

    def remove(self):
        try:
            running_containers = self.docker_client.containers.list()
            for container in running_containers:
                if container.name == self.container_name:
                    container.remove(force=True)
        except Exception as e:
            self.logger.log(
                logging.DEBUG, {"event": "Server.remove", "stage": "end", "error": str(e)}
            )

    def runner(self):
        while True:
            try:
                if self.chaos:
                    self.start()
                    to_run = random.randint(  # nosec
                        self.container_min_run_duration, self.container_max_run_duration
                    )
                    to_run = to_run * 60
                    self.logger.log(
                        logging.INFO,
                        {
                            "event": "Server.runner",
                            "stage": "start",
                            "state": "container to run for {0} minutes".format(to_run / 60),
                        },
                    )
                    time.sleep(to_run)  # keep container running for this long secs

                    self.stop()
                    to_stop = random.randint(  # nosec
                        self.container_min_stop_duration, self.container_max_stop_duration
                    )
                    to_stop = to_stop * 60
                    self.logger.log(
                        logging.INFO,
                        {
                            "event": "Server.runner",
                            "stage": "start",
                            "state": "container to stop for {0} minutes".format(to_stop / 60),
                        },
                    )
                    time.sleep(to_stop)  # keep container in a stopped state for this long secs
                else:
                    # run forever
                    self.start()
                    to_run = 168 * 60 * 60  # 7days
                    self.logger.log(
                        logging.INFO,
                        {
                            "event": "Server.runner",
                            "stage": "start",
                            "state": "container to run for {0} minutes".format(to_run / 60),
                        },
                    )
                    time.sleep(to_run)  # keep container running for this long secs
            except Exception as e:
                self.logger.log(
                    logging.ERROR, {"event": "Server.runner", "stage": "end", "error": str(e)}
                )
                raise e


if __name__ == "__main__":
    RedisServer = Server(
        image_name="redis:5.0-alpine",
        container_name="naz_benchmarks_RedisServer",
        labels={"name": "redis_server", "use": "running_naz_benchmarks"},
        ports={"6379/tcp": 6379},
        command="redis-server --requirepass {0}".format(os.environ["REDIS_PASSWORD"]),
    )
    redis_thread = threading.Thread(
        target=RedisServer.runner, name="Thread-<redis_naz_benchmarks_server>", daemon=True
    )
    redis_thread.start()

    SmppServer = Server(
        image_name="komuw/smpp_server:v0.3",
        container_name="naz_benchmarks_SmppServer",
        labels={"name": "smpp_server", "use": "running_naz_benchmarks"},
        ports={"2775/tcp": 2775, "8884/tcp": 8884},
    )
    SmppServer.runner()

import sys
import typing
import logging

import naz

import prometheus_client


class BenchmarksHook(naz.hooks.BaseHook):
    """
    This is an implementation of BaseHook.

    When this hook is called by `naz` it sends metrics to prometheus.
    """

    def __init__(self) -> None:
        self.registry = prometheus_client.CollectorRegistry()
        _labels = ["project", "smpp_command", "state"]
        self.counter = prometheus_client.Counter(
            name="number_of_messages",
            documentation="number of messages processed by naz.",
            labelnames=_labels,
            registry=self.registry,
        )

        self.logger = naz.logger.SimpleLogger("naz_benchmarks.BenchmarksHook")

        # go to prometheus dashboard(http://localhost:9000/) & you can run queries like:
        # 1. container_memory_rss{name="naz_cli", container_label_com_docker_compose_service="naz_cli"}
        # 2. container_memory_rss{name=~"naz_cli|message_producer"}
        # 3. number_of_tasks_total{state=~"EXECUTED|QUEUED"}
        # 4. rate(number_of_tasks_total{task_name="MemTask"}[30s]) # task execution/queueing rate over the past 30seconds

    async def request(self, smpp_command: str, log_id: str, hook_metadata: str) -> None:
        self.logger.log(
            logging.INFO,
            {
                "event": "BenchmarksHook.request",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
            },
        )
        self.counter.labels(
            project="naz_benchmarks", smpp_command=smpp_command, state="request"
        ).inc()  # Increment by 1
        self._publish()

    async def response(
        self, smpp_command: str, log_id: str, hook_metadata: str, smsc_response: naz.CommandStatus
    ) -> None:
        self.logger.log(
            logging.INFO,
            {
                "event": "BenchmarksHook.response",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
                "smsc_response_description": smsc_response.description,
                "smsc_response_code": smsc_response.code,
            },
        )
        self.counter.labels(
            project="naz_benchmarks", smpp_command=smpp_command, state="request"
        ).inc()  # Increment by 1
        self._publish()

    def _publish(self):
        prometheus_client.push_to_gateway(
            "push_to_gateway:9091", job="BenchmarksHook", registry=self.registry
        )


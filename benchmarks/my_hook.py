import asyncio
import logging
import functools
import concurrent

import naz

import prometheus_client


class BenchmarksHook(naz.hooks.BaseHook):
    """
    This is an implementation of BaseHook.

    When this hook is called by `naz` it sends metrics to prometheus.
    """

    def __init__(self) -> None:
        self.registry = prometheus_client.CollectorRegistry()
        _labels = ["project", "smpp_command", "state", "response_code"]
        self.counter = prometheus_client.Counter(
            name="number_of_messages",
            documentation="number of messages processed by naz.",
            labelnames=_labels,
            registry=self.registry,
        )

        self.logger = naz.logger.SimpleLogger("naz_benchmarks.BenchmarksHook")
        self.loop = asyncio.get_event_loop()
        self.thread_name_prefix = "naz_benchmarks_hook_pool"

        # go to prometheus dashboard(http://localhost:9000/) & you can run queries like:
        # 1. container_memory_rss{name="naz_cli", container_label_com_docker_compose_service="naz_cli"}
        # 2. container_memory_rss{name=~"naz_cli|message_producer"}
        # 3. number_of_messages_total{project="naz_benchmarks"}
        # 4. rate(number_of_messages_total{smpp_command="submit_sm",state="request"}[30s])  # msg sending over the past 30seconds

    async def request(self, smpp_command: str, log_id: str, hook_metadata: str) -> None:
        # self.logger.log(
        #     logging.INFO,
        #     {
        #         "event": "BenchmarksHook.request",
        #         "stage": "start",
        #         "smpp_command": smpp_command,
        #         "log_id": log_id,
        #         "hook_metadata": hook_metadata,
        #     },
        # )
        self.counter.labels(
            project="naz_benchmarks",
            smpp_command=smpp_command,
            state="request",
            response_code="",  # this is a request so there's no response_code
        ).inc()
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix=self.thread_name_prefix
        ) as executor:
            await self.loop.run_in_executor(executor, functools.partial(self._publish))

    async def response(
        self, smpp_command: str, log_id: str, hook_metadata: str, smsc_response: naz.CommandStatus
    ) -> None:
        # self.logger.log(
        #     logging.INFO,
        #     {
        #         "event": "BenchmarksHook.response",
        #         "stage": "start",
        #         "smpp_command": smpp_command,
        #         "log_id": log_id,
        #         "hook_metadata": hook_metadata,
        #         "smsc_response_description": smsc_response.description,
        #         "smsc_response_code": smsc_response.code,
        #     },
        # )
        self.counter.labels(
            project="naz_benchmarks",
            smpp_command=smpp_command,
            state="response",
            response_code=smsc_response.code,
        ).inc()  # Increment by 1
        with concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix=self.thread_name_prefix
        ) as executor:
            await self.loop.run_in_executor(executor, functools.partial(self._publish))

    def _publish(self):
        """
        push metrics out to a place where prometheus can scrape.
        """
        prometheus_client.push_to_gateway(
            "push_to_gateway:9091", job="BenchmarksHook", registry=self.registry
        )

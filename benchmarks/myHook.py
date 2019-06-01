import sys
import typing
import logging

import wiji

import prometheus_client


class BenchmarksHook(wiji.hook.BaseHook):
    def __init__(self) -> None:
        self.logger = wiji.logger.SimpleLogger("wiji.benchmarks.BenchmarksHook")

        self.registry = prometheus_client.CollectorRegistry()
        _labels = ["library", "task_name", "state"]
        self.counter = prometheus_client.Counter(
            name="number_of_tasks",
            documentation="number of tasks processed by wiji.",
            labelnames=_labels,
            registry=self.registry,
        )

        # go to prometheus dashboard(http://localhost:9000/) & you can run queries like:
        # 1. container_memory_rss{name="wiji_cli", container_label_com_docker_compose_service="wiji_cli"}
        # 2. container_memory_rss{name=~"wiji_cli|task_producer"}
        # 3. number_of_tasks_total{state=~"EXECUTED|QUEUED"}
        # 4. rate(number_of_tasks_total{task_name="MemTask"}[30s]) # task execution/queueing rate over the past 30seconds

    async def notify(
        self,
        task_name: str,
        task_id: str,
        queue_name: str,
        hook_metadata: str,
        state: wiji.task.TaskState,
        queuing_duration: typing.Union[None, typing.Dict[str, float]] = None,
        queuing_exception: typing.Union[None, Exception] = None,
        execution_duration: typing.Union[None, typing.Dict[str, float]] = None,
        execution_exception: typing.Union[None, Exception] = None,
        return_value: typing.Union[None, typing.Any] = None,
    ) -> None:
        try:
            if not isinstance(queuing_exception, type(None)):
                raise ValueError(
                    "task Queuing produced error. task_name={0}".format(task_name)
                ) from queuing_exception
        except Exception as e:
            # yep, we are serious that this benchmarks should complete without error
            # else we exit
            self.logger.log(
                logging.ERROR,
                {
                    "event": "wiji.BenchmarksHook.notify",
                    "stage": "end",
                    "error": str(e),
                    "state": state,
                    "task_name": task_name,
                    "queue_name": queue_name,
                    "queuing_exception": str(queuing_exception),
                },
            )
            sys.exit(97)
        try:
            if not isinstance(execution_exception, type(None)):
                raise ValueError(
                    "task Execution produced error. task_name={0}".format(task_name)
                ) from execution_exception
        except Exception as e:
            # yep, we are serious that this benchmarks should complete without error
            # else we exit
            self.logger.log(
                logging.ERROR,
                {
                    "event": "wiji.BenchmarksHook.notify",
                    "stage": "end",
                    "error": str(e),
                    "state": state,
                    "task_name": task_name,
                    "queue_name": queue_name,
                    "execution_exception": str(execution_exception),
                    "return_value": str(return_value),
                },
            )
            sys.exit(98)

        try:
            if state == wiji.task.TaskState.QUEUED:
                self.counter.labels(
                    library="wiji", task_name=queue_name, state=wiji.task.TaskState.QUEUED.name
                ).inc()  # Increment by 1
                self.logger.log(
                    logging.DEBUG,
                    {
                        "event": "wiji.BenchmarksHook.notify",
                        "state": state,
                        "task_name": task_name,
                        "queue_name": queue_name,
                    },
                )

            elif state == wiji.task.TaskState.EXECUTED:
                self.counter.labels(
                    library="wiji", task_name=queue_name, state=wiji.task.TaskState.EXECUTED.name
                ).inc()  # Increment by 1
                self.logger.log(
                    logging.DEBUG,
                    {
                        "event": "wiji.BenchmarksHook.notify",
                        "stage": "start",
                        "state": state,
                        "task_name": task_name,
                        "queue_name": queue_name,
                        "execution_exception": str(execution_exception),
                        "return_value": str(return_value),
                    },
                )
        except Exception as e:
            # yep, we are serious that this benchmarks should complete without error
            # else we exit
            self.logger.log(
                logging.ERROR,
                {
                    "event": "wiji.BenchmarksHook.notify",
                    "stage": "end",
                    "error": str(e),
                    "state": state,
                    "task_name": task_name,
                    "queue_name": queue_name,
                },
            )
            sys.exit(99)
        finally:
            prometheus_client.push_to_gateway(
                "push_to_gateway:9091", job="BenchmarksHook", registry=self.registry
            )

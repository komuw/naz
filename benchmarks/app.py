import os
import typing
import logging

import naz

from my_hook import BenchmarksHook
from redis_queue import MyRedisQueue


# run as:
#   naz-cli --client benchmarks.app.my_naz_client


class MyLogger(naz.logger.SimpleLogger):
    def bind(self, level: typing.Union[str, int], log_metadata: dict) -> None:
        level = self._nameToLevel(level=level)
        self._logger = logging.getLogger(self.logger_name)
        formatter = logging.Formatter("%(message)s")

        handler1 = logging.FileHandler(filename="/tmp/namedPipes/naz_log_named_pipe")
        handler1.setFormatter(formatter)
        handler1.setLevel(level)
        self._logger.addHandler(handler1)

        handler2 = logging.StreamHandler()
        handler2.setFormatter(formatter)
        handler2.setLevel(level)
        self._logger.addHandler(handler2)

        self._logger.setLevel(level)
        self.logger: logging.LoggerAdapter = naz.logger.NazLoggingAdapter(
            self._logger, log_metadata
        )


country_code = "254"

my_naz_client = naz.Client(
    smsc_host=os.getenv("smsc_server", "smsc_server"),
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
    loglevel="DEBUG",
    log_metadata={"project": "naz_benchmarks"},
    outboundqueue=MyRedisQueue(),
    hook=BenchmarksHook(),
    log_handler=MyLogger("naz.client"),
    connect_timeout=15.00,
    enquire_link_interval=80.00,
    address_range="^{0}".format(
        country_code
    ),  # any msisdns beginning with 254. See Appendix A of smpp spec
)

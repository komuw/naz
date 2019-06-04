import json
import typing
import logging

import naz


class MyLogAdapter(naz.logger.NazLoggingAdapter):
    def process(self, msg, kwargs):
        timestamp = self.formatTime()
        if isinstance(msg, str):
            merged_msg = "{0} {1} {2}".format(timestamp, msg, self.extra)
            if self.extra == {}:
                merged_msg = "{0} {1}".format(timestamp, msg)
            return self._dumps(merged_msg), kwargs
        else:
            _timestamp = {"timestamp": timestamp}
            merged_msg = {**_timestamp, **msg, **self.extra}
            return self._dumps(merged_msg), kwargs

    def _dumps(self, merged_msg):
        try:
            return json.dumps(merged_msg)
        except Exception as e:
            return self._dumps(str(e))


class BenchmarksLogger(naz.logger.SimpleLogger):
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
        self.logger: logging.LoggerAdapter = MyLogAdapter(self._logger, log_metadata)

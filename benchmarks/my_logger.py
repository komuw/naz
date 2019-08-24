import os
import errno
import json
import typing
import logging

import naz


def makelog(log_directory="/usr/src/nazLog", log_file="naz_log_file"):
    log_file = os.path.join(log_directory, log_file)
    if os.path.exists(log_file):
        # we want a new file at start-up
        os.remove(log_file)

    try:
        os.mkdir(log_directory, mode=0o777)
    except OSError as e:
        if e.errno == 17:
            # File exists
            pass
        else:
            raise e

    try:
        f = open(log_file, "a")
        f.close()
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    return log_file


log_file = makelog()


class MyLogAdapter(naz.log._NazLoggingAdapter):
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


class BenchmarksLogger(naz.log.SimpleLogger):
    def bind(self, level: typing.Union[str, int], log_metadata: dict) -> None:
        level = self._nameToLevel(level=level)
        self._logger = logging.getLogger(self.logger_name)
        formatter = logging.Formatter("%(message)s")

        handler1 = logging.FileHandler(filename=log_file)
        handler1.setFormatter(formatter)
        handler1.setLevel(logging.DEBUG)
        self._logger.addHandler(handler1)

        # this may have been causing the issue mentioned at:
        #  - https://github.com/komuw/naz/issues/103#issuecomment-500208481
        # handler2 = logging.StreamHandler()
        # handler2.setFormatter(formatter)
        # handler2.setLevel(level)
        # self._logger.addHandler(handler2)

        self._logger.setLevel(level)
        self.logger: logging.LoggerAdapter = MyLogAdapter(self._logger, log_metadata)

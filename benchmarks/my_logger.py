import os
import errno
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


class BenchmarksLogger(naz.log.SimpleLogger):
    def __init__(
        self,
        logger_name: str,
        level: typing.Union[str, int] = logging.INFO,
        log_metadata: typing.Union[None, dict] = None,
        handler: typing.Union[None, logging.Handler] = None,
    ) -> None:
        super(BenchmarksLogger, self).__init__(logger_name, level, log_metadata, handler)
        formatter = logging.Formatter("%(message)s")
        handler2 = logging.FileHandler(filename=log_file)
        handler2.setFormatter(formatter)
        handler2.setLevel(self.level)
        self.addHandler(handler2)

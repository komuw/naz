import logging


class BaseLogger:
    def register(self, loglevel: str, log_metadata: dict) -> None:
        raise NotImplementedError("register method must be implemented.")

    def log(self, level: int, log_data: dict) -> None:
        raise NotImplementedError("log method must be implemented.")


class SimpleBaseLogger(BaseLogger):
    def register(self, loglevel: str, log_metadata: dict) -> None:
        self._logger = logging.getLogger("naz.client")
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self._logger.handlers:
            self._logger.addHandler(handler)
        self._logger.setLevel(loglevel)
        self.logger: logging.LoggerAdapter = NazLoggingAdapter(self._logger, log_metadata)

    def log(self, level: int, log_data: dict) -> None:
        self.logger.log(level, log_data)


class NazLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if isinstance(msg, str):
            return msg, kwargs
        else:
            merged_log_event = {**msg, **self.extra}
            return "{0}".format(merged_log_event), kwargs


#### trial:
# # TODO: remove
# log_metadata = {"name": "komu", "age": 90}
# logger = SimpleBaseLogger()
# logger.register("DEBUG", log_metadata)
# logger.log(logging.INFO, {"event": "naz.Client.tranceiver_bind", "stage": "start"})

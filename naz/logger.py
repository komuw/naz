import logging


class NazLoggingAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'log_metadata' key, whose value in brackets is apended to the log message.
    """

    def process(self, msg, kwargs):
        if isinstance(msg, str):
            return msg, kwargs
        else:
            log_metadata = self.extra.get("log_metadata")
            merged_log_event = {**msg, **log_metadata}
            return "{0}".format(merged_log_event), kwargs

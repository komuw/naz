import naz
from examples.example_klasses import ExampleRedisQueue, MySeqGen, MyRateLimiter


# run as:
#  naz-cli --client examples.example_config.client

import logging


class Hook(naz.hooks.BaseHook):
    def __init__(self):
        self.logger = naz.log.SimpleLogger("MyHook")

    async def request(self, smpp_command, log_id, hook_metadata):
        self.logger.log(
            logging.INFO,
            {
                "event": "naz.SimpleHook.request",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
            },
        )

    async def response(self, smpp_command, log_id, hook_metadata, smsc_response, pdu):
        self.logger.log(
            logging.INFO,
            {
                "event": "naz.SimpleHook.response",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "hook_metadata": hook_metadata,
                "smsc_response": smsc_response,
                "pdu": pdu,
            },
        )


client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=ExampleRedisQueue(),
    encoding="gsm0338",
    sequence_generator=MySeqGen(),
    loglevel="INFO",
    log_metadata={"environment": "staging", "release": "canary"},
    codec_errors_level="ignore",
    enquire_link_interval=70.00,
    rateLimiter=MyRateLimiter(),
    address_range="^254",  # any msisdns beginning with 254. See Appendix A of SMPP spec doc
    logger=naz.log.SimpleLogger("custom_logger", handler=naz.log.BreachHandler()),
    hook=Hook(),
)

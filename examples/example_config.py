import naz
from examples.example_klasses import ExampleRedisBroker, MySeqGen, MyRateLimiter


# run as:
#  naz-cli --client examples.example_config.client
client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    broker=ExampleRedisBroker(),
    sequence_generator=MySeqGen(),
    logger=naz.log.SimpleLogger(
        "naz.client", level="INFO", log_metadata={"environment": "staging", "release": "canary"}
    ),
    enquire_link_interval=70.00,
    rateLimiter=MyRateLimiter(),
    address_range="^254",  # any msisdns beginning with 254. See Appendix A of SMPP spec doc
)

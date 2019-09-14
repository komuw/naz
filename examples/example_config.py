import naz
from examples.example_klasses import ExampleRedisQueue, MySeqGen, MyRateLimiter


# run as:
#  naz-cli --client examples.example_config.client
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
)

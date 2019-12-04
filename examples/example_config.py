import naz
from examples.example_klasses import ExampleRedisBroker  # , MySeqGen, MyRateLimiter


# run as:
#  naz-cli --client examples.example_config.client
client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    broker=ExampleRedisBroker(),
    codec=naz.codec.SimpleCodec(encoding="ucs2"),
    socket_timeout=4.00,
    logger=naz.log.SimpleLogger("example_config.client", render_as_json=False),
)

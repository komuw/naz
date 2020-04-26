import naz
from examples.example_klasses import ExampleRedisBroker  # , MySeqGen, MyRateLimiter
import codecs

# run as:
#  naz-cli --client examples.example_config.client
client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    broker=ExampleRedisBroker(),
    socket_timeout=4.00,
    logger=naz.log.SimpleLogger("example_config.client", render_as_json=False),
    enquire_link_interval=59.00,
    address_range="254722111111",  # any msisdns beginning with 254. See Appendix A of smpp spec
    custom_codecs={
        "shift_jis": codecs.CodecInfo(
            name="ucs2", encode=naz.codec.UCS2Codec.encode, decode=naz.codec.UCS2Codec.decode
        ),
    },
)

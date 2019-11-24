import naz
from examples.example_klasses import ExampleRedisBroker, MySeqGen, MyRateLimiter
from pythonfuzz.main import PythonFuzz

import asyncio


# run as:
#  naz-cli --client examples.example_config.client
client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    broker=ExampleRedisBroker(),
    # sequence_generator=MySeqGen(),
    loglevel="INFO",
    log_metadata={"environment": "staging", "release": "canary"},
    enquire_link_interval=70.00,
    # rateLimiter=MyRateLimiter(),
    address_range="^254",  # any msisdns beginning with 254. See Appendix A of SMPP spec doc
)


@PythonFuzz
def fuzz(buf):
    # try:
    print("\n\n\t buf   ", buf)
    asyncio.run(asyncMain(buf=buf))
    # except UnicodeDecodeError:
    #     pass


async def asyncMain(buf):
    # _string = "zz"

    # zzz = buf.decode()
    await client.connect()
    client.current_session_state = naz.SmppSessionState.BOUND_TRX
    await client._parse_response_pdu(pdu=buf)


if __name__ == "__main__":
    fuzz()

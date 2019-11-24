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

    # 1.
    _msg_to_log(buf)

    # 2.
    await send_data(
        smpp_command="smpp_command", msg=buf, log_id="log_id", hook_metadata="hook_metadata"
    )

    # 3.
    await _parse_response_pdu(pdu=buf)

    # 4.
    await command_handlers(
        pdu=buf,
        body_data=body_data,
        smpp_command=smpp_command,
        command_status_value=5,
        sequence_number=78,
        log_id="log_id",
        hook_metadata="hook_metadata",
    )


def _msg_to_log(msg: bytes):
    client._msg_to_log(msg=msg)


async def send_data(smpp_command: str, msg: bytes, log_id: str, hook_metadata: str = ""):
    await client.send_data(
        smpp_command=smpp_command, msg=msg, log_id=log_id, hook_metadata=hook_metadata
    )


async def _parse_response_pdu(pdu: bytes) -> None:
    await client._parse_response_pdu(pdu=pdu)


async def command_handlers(
    pdu: bytes,
    body_data: bytes,
    smpp_command: str,
    command_status_value: int,
    sequence_number: int,
    log_id: str,
    hook_metadata: str,
) -> None:
    await client.command_handlers(
        pdu=pdu,
        body_data=body_data,
        smpp_command=smpp_command,
        command_status_value=command_status_value,
        sequence_number=sequence_number,
        log_id=log_id,
        hook_metadata=hook_metadata,
    )


if __name__ == "__main__":
    fuzz()

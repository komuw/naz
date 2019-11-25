import sys
import naz
import random
from examples.example_klasses import ExampleRedisBroker
from pythonfuzz.main import PythonFuzz

import asyncio


# run as:
#    python tests/fuzz.py parse_response_pdu
client = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    broker=ExampleRedisBroker(),
    enquire_link_interval=70.00,
    logger=naz.log.SimpleLogger(
        "naz.fuzz", level="INFO", log_metadata={"environment": "staging", "release": "canary"},
    ),
)

FUNCTIONALITIES = ["msg_to_log", "send_data", "parse_response_pdu", "command_handlers"]
FUNCTIONALITY_TO_FUZZ = None


@PythonFuzz
def fuzz(buf):
    smpp_command = random.choice(
        [
            naz.SmppCommand.BIND_TRANSCEIVER,
            naz.SmppCommand.BIND_TRANSCEIVER_RESP,
            naz.SmppCommand.BIND_TRANSMITTER,
            naz.SmppCommand.BIND_RECEIVER,
            naz.SmppCommand.UNBIND,
            naz.SmppCommand.UNBIND_RESP,
            naz.SmppCommand.SUBMIT_SM,
            naz.SmppCommand.SUBMIT_SM_RESP,
            naz.SmppCommand.DELIVER_SM,
            naz.SmppCommand.DELIVER_SM_RESP,
            naz.SmppCommand.ENQUIRE_LINK,
            naz.SmppCommand.ENQUIRE_LINK_RESP,
            naz.SmppCommand.GENERIC_NACK,
        ]
    )

    print("\n\n\t buf: ", buf)
    print("smpp_command: ", smpp_command)
    print("FUNCTIONALITY_TO_FUZZ: ", FUNCTIONALITY_TO_FUZZ)
    print()
    asyncio.run(
        asyncMain(buf=buf, smpp_command=smpp_command, FUNCTIONALITY_TO_FUZZ=FUNCTIONALITY_TO_FUZZ)
    )


async def asyncMain(buf, smpp_command, FUNCTIONALITY_TO_FUZZ):
    await client.connect()
    client.current_session_state = naz.SmppSessionState.BOUND_TRX

    if FUNCTIONALITY_TO_FUZZ == "msg_to_log":
        # 1.msg_to_log
        _msg_to_log(buf)
    elif FUNCTIONALITY_TO_FUZZ == "send_data":
        # 2.send_data
        await send_data(
            smpp_command=smpp_command, msg=buf, log_id="log_id", hook_metadata="hook_metadata"
        )
    elif FUNCTIONALITY_TO_FUZZ == "parse_response_pdu":
        # 3.parse_response_pdu
        await _parse_response_pdu(pdu=buf)
    elif FUNCTIONALITY_TO_FUZZ == "command_handlers":
        # 4.command_handlers
        await command_handlers(
            pdu=buf,
            body_data=buf,
            smpp_command=smpp_command,
            command_status_value=5,
            sequence_number=78,
            log_id="log_id",
            hook_metadata="hook_metadata",
        )
    else:
        raise ValueError("unknown functionality {0}".format(FUNCTIONALITY_TO_FUZZ))


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
    functionality = sys.argv[1]
    if functionality not in FUNCTIONALITIES:
        raise ValueError("unknown functionality. choose on of {0}".format(FUNCTIONALITIES))

    FUNCTIONALITY_TO_FUZZ = functionality

    fuzz()

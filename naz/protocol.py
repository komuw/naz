import json
import typing

from . import state

# 1.
# item_to_enqueue = {
#             "version": self.naz_message_protocol_version,
#             "smpp_command": smpp_command,
#             "log_id": log_id,
#             "pdu": full_pdu,

#         }

# 2.
#  item_to_enqueue = {
#             "version": self.naz_message_protocol_version,
#              "smpp_command": smpp_command,
#             "log_id": log_id,
#             "pdu": full_pdu,

#         }

# 3.
#  item_to_enqueue = {
#             "version": self.naz_message_protocol_version,
#             "smpp_command": smpp_command,
#             "short_message": short_message,
#             "log_id": log_id,
#             "source_addr": source_addr,
#             "destination_addr": destination_addr,
#         }

# 4.
# '{"version": "1",
# "smpp_command": "submit_sm",
# "short_message": "Hello. Thanks for subscribing to our service.",
# "log_id": "iEKas812k",
# "source_addr": "254722000000",
# "destination_addr": "254722111111",
# "hook_metadata": "{\\"telco\\": \\"verizon\\", \\"customer_id\\": 123456}"
# }'
class Protocol:
    def __init__(
        self,
        version: int,
        smpp_command: state.SmppCommand,
        log_id: str,
        pdu: typing.Union[None, bytes],
        short_message: typing.Union[None, str],
        source_addr: str,
        destination_addr: str,
        hook_metadata: str,
    ) -> None:
        self._validate_protocol_args(
            version=version,
            smpp_command=smpp_command,
            log_id=log_id,
            pdu=pdu,
            short_message=short_message,
            source_addr=source_addr,
            destination_addr=destination_addr,
            hook_metadata=hook_metadata,
        )
        self.version = version
        self.smpp_command = smpp_command
        self.log_id = log_id
        self.pdu = pdu
        self.short_message = short_message
        self.source_addr = source_addr
        self.destination_addr = destination_addr
        self.hook_metadata = hook_metadata

    def _validate_protocol_args(
        self,
        version: int,
        smpp_command: state.SmppCommand,
        log_id: str,
        pdu: typing.Union[None, bytes],
        short_message: typing.Union[None, str],
        source_addr: str,
        destination_addr: str,
        hook_metadata: str,
    ):
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if not isinstance(smpp_command, state.SmppCommand):
            raise ValueError(
                "`smpp_command` should be of type:: `naz.state.SmppCommand` You entered: {0}".format(
                    type(smpp_command)
                )
            )
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(pdu, (type(None), bytes)):
            raise ValueError(
                "`pdu` should be of type:: `None` or `bytes` You entered: {0}".format(type(pdu))
            )
        if not isinstance(short_message, (type(None), str)):
            raise ValueError(
                "`short_message` should be of type:: `None` or `str` You entered: {0}".format(
                    type(short_message)
                )
            )
        # TODO: validate that short_message and pdu are mutually exclusive
        if not isinstance(source_addr, str):
            raise ValueError(
                "`source_addr` should be of type:: `str` You entered: {0}".format(type(source_addr))
            )
        if not isinstance(destination_addr, str):
            raise ValueError(
                "`destination_addr` should be of type:: `str` You entered: {0}".format(
                    type(destination_addr)
                )
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )

    def json(self) -> str:
        # because pdu is in bytes, when converting to string; we need to use whatever encoding was passed in
        # to naz.Client
        return json.dumps({"version": self.version, smpp_command: self.smpp_command})

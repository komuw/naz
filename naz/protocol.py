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
    def __init__(self, version: int, smpp_command: state.SmppCommand) -> None:
        self._validate_protocol_args(version=version, smpp_command=smpp_command)
        self.version = version
        self.smpp_command = smpp_command

    def _validate_protocol_args(self, version: int, smpp_command: state.SmppCommand):
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

    def json(self) -> str:
        return json.dumps({"version": self.version, smpp_command: self.smpp_command})

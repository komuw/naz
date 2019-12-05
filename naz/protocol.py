from __future__ import annotations

import json
import typing


class Message:
    """
    The message protocol for `naz`. It is the code representation of what
    gets queued into a naz broker.

    Usage:

    .. highlight:: python
    .. code-block:: python

        import naz
        msg = naz.protocol.Message(
            version=1,
            smpp_command=naz.SmppCommand.SUBMIT_SM,
            log_id="some-log-id",
            short_message="Hello, thanks for shopping with us.",
            source_addr="254722111111",
            destination_addr="254722999999",
        )
    """

    # all messages in `naz` protocol are encoded as `utf8`.
    # This is even though the `pdu` passed into this class is a byte that may contain different SMSC fields that are encoded using different schemes.
    # Some fields may be `struct.pack(">I")` others `.encode("ascii")` and still others `codec.encode("ucs2")`
    ENCODING = "utf8"

    def __init__(
        self,
        version: int,
        smpp_command: str,
        log_id: str,
        pdu: typing.Union[None, bytes] = None,
        short_message: typing.Union[None, str] = None,
        source_addr: typing.Union[None, str] = None,
        destination_addr: typing.Union[None, str] = None,
        hook_metadata: typing.Union[None, str] = None,
    ) -> None:
        """
        Parameters:
            version: This indicates the current version of the naz message protocol. This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            smpp_command: any one of the SMSC commands eg submit_sm
            log_id: a unique identify of this reque
            pdu: the full PDU as sent to SMSC. It is mutually exclusive with `short_message`.
                 Note that the pdu is a byte that may contain different SMSC fields that are encoded using different schemes.
                 Some fields may be `struct.pack(">I")` others `.encode("ascii")` and still others `codec.encode("ucs2")`
            short_message: message to send to SMSC. It is mutually exclusive with `pdu`
            source_addr: the identifier(eg msisdn) of the message sender.
            destination_addr: the identifier(eg msisdn) of the message receiver.
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
        """
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
        smpp_command: str,
        log_id: str,
        pdu: typing.Union[None, bytes],
        short_message: typing.Union[None, str],
        source_addr: typing.Union[None, str],
        destination_addr: typing.Union[None, str],
        hook_metadata: typing.Union[None, str],
    ):
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if not isinstance(smpp_command, str):
            raise ValueError(
                "`smpp_command` should be of type:: `str` You entered: {0}".format(
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
        if pdu and short_message:
            raise ValueError("You cannot specify both `pdu` and `short_message`")
        if not isinstance(source_addr, (type(None), str)):
            raise ValueError(
                "`source_addr` should be of type:: `None` or `str` You entered: {0}".format(
                    type(source_addr)
                )
            )
        if not isinstance(destination_addr, (type(None), str)):
            raise ValueError(
                "`destination_addr` should be of type:: `None` or `str` You entered: {0}".format(
                    type(destination_addr)
                )
            )
        if not isinstance(hook_metadata, (type(None), str)):
            raise ValueError(
                "`hook_metadata` should be of type:: `None` or `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )

    def to_json(self) -> str:
        """
        Serializes the message protocol to json. You can use this method if you would
        like to save the `Message` into a broker like redis/rabbitmq/postgres etc.
        """
        _item = {
            "version": self.version,
            "smpp_command": self.smpp_command,
            "log_id": self.log_id,
            "pdu": self.pdu,
            "short_message": self.short_message,
            "source_addr": self.source_addr,
            "destination_addr": self.destination_addr,
            "hook_metadata": self.hook_metadata,
        }
        if self.pdu:
            _item["pdu"] = self.pdu.decode(self.ENCODING)

        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> Message:
        """
        Deserializes the message protocol from json. You can use this method if you would
        like to return the `Message` from a broker like redis/rabbitmq/postgres etc.

        Parameters:
            json_message: `naz.protocol.Message` in json format.
        """
        _in_dict = json.loads(json_message)
        if _in_dict.get("pdu"):
            # we need to convert pdu to bytes.
            # all valid `naz` protocol messages are encoded/decoded with `Message.ENCODING` scheme.
            # There's a risk of a message having been encoded with another encoding other than `Message.ENCODING` when been saved to broker
            # However, this risk is small and we should only consider it if people report it as a bug.
            _in_dict["pdu"] = _in_dict["pdu"].encode(Message.ENCODING)

        return Message(**_in_dict)

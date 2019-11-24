import json
import typing

from . import state
from . import nazcodec

# TODO:
# - rename protocol to MessageProtocol
# - delete config.md


class Message:
    def __init__(
        self,
        version: int,
        smpp_command: state.SmppCommand,
        log_id: str,
        pdu: typing.Union[None, bytes] = None,
        codec_class: typing.Union[None, nazcodec.BaseNazCodec] = None,
        short_message: typing.Union[None, str] = None,
        source_addr: typing.Union[None, str] = None,
        destination_addr: typing.Union[None, str] = None,
        hook_metadata: typing.Union[None, str] = None,
    ) -> None:
        self._validate_protocol_args(
            version=version,
            smpp_command=smpp_command,
            log_id=log_id,
            pdu=pdu,
            codec_class=codec_class,
            short_message=short_message,
            source_addr=source_addr,
            destination_addr=destination_addr,
            hook_metadata=hook_metadata,
        )
        self.version = version
        self.smpp_command = smpp_command
        self.log_id = log_id
        self.pdu = pdu
        self.codec_class = codec_class
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
        codec_class: typing.Union[None, nazcodec.BaseNazCodec],
        short_message: typing.Union[None, str],
        source_addr: typing.Union[None, str],
        destination_addr: typing.Union[None, str],
        hook_metadata: typing.Union[None, str],
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
        if not isinstance(codec_class, (type(None), nazcodec.BaseNazCodec)):
            raise ValueError(
                "`codec_class` should be of type:: `None` or `naz.nazcodec.BaseNazCodec` You entered: {0}".format(
                    type(codec_class)
                )
            )
        if pdu and not codec_class:
            raise ValueError("You cannot specify `pdu` and not a `codec_class`")

    def json(self) -> str:
        # because pdu is in bytes, when converting to string; we need to use whatever encoding was passed in
        # to naz.Client

        return json.dumps(
            {
                "version": self.version,
                "smpp_command": self.smpp_command.value,
                "log_id": self.log_id,
                "pdu": self.codec_class.decode(self.pdu),
                "short_message": self.short_message,
                "source_addr": self.source_addr,
                "destination_addr": self.destination_addr,
                "hook_metadata": self.hook_metadata,
            }
        )


# self.codec_class.decode(_message_id, self.encoding, self.codec_errors_level)

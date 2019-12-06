import abc
import json

from . import state


NAZ_MESSAGE_PROTOCOL_VERSION = 1
"""
The messages that are published to a queue by either naz
or user application should be versioned.
This version will enable naz to be able to evolve in future;
eg a future version of naz could add/remove the number of required items in a message.
This is a bit similar to: http://docs.celeryproject.org/en/latest/internals/protocol.html
"""


class Message(abc.ABC):
    """
    The message protocol for `naz`. It is the code representation of what
    gets queued into a naz broker.
    This is the interface that must be implemented to satisfy naz's message protocol.

    Users should only ever have to deal with the :class:`SubmitSM <SubmitSM>` implementation
    """

    @abc.abstractmethod
    def __init__(
        self, version: int, smpp_command: str, log_id: str, hook_metadata: str = ""
    ) -> None:
        """
        Parameters:
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            smpp_command: any one of the SMSC commands eg submit_sm
            log_id: a unique identify of this request
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
        """
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
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
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        self.version = version
        self.smpp_command = smpp_command
        self.log_id = log_id
        self.hook_metadata = hook_metadata

    @abc.abstractmethod
    def to_json(self) -> str:
        """
        Serializes the message protocol to json. You can use this method if you would
        like to save the `Message` into a broker like redis/rabbitmq/postgres etc.
        """
        raise NotImplementedError("to_json method must be implemented.")

    @staticmethod
    @abc.abstractmethod
    def from_json(json_message: str) -> "Message":
        """
        Deserializes the message protocol from json.

        Parameters:
            json_message: `naz.protocol.Message` in json format.
        """
        raise NotImplementedError("from_json method must be implemented.")


class SubmitSM(Message):
    """
    The code representation of the `submit_sm` pdu that will get queued into a broker.

    Usage:

    .. highlight:: python
    .. code-block:: python

        import naz

        broker = naz.broker.SimpleBroker(maxsize=1000)
        client = naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=broker,
            )
        msg = naz.protocol.SubmitSM(
            short_message="hello world",
            source_addr="255700111222",
            destination_addr="255799000888",
            log_id="some-id",
        )
        await client.send_message(msg)
    """

    def __init__(
        self,
        short_message: str,
        source_addr: str,
        destination_addr: str,
        log_id: str,
        version: int = 1,
        smpp_command: str = state.SmppCommand.SUBMIT_SM,
        hook_metadata: str = "",
        service_type: str = "CMT",  # section 5.2.11
        source_addr_ton: int = 0x00000001,  # section 5.2.5
        source_addr_npi: int = 0x00000001,
        dest_addr_ton: int = 0x00000001,
        dest_addr_npi: int = 0x00000001,
        # xxxxxx00 store-and-forward
        # xx0010xx Short Message contains ESME Delivery Acknowledgement
        # 00xxxxxx No specific features selected
        esm_class: int = 0b00000011,  # section 5.2.12
        protocol_id: int = 0x00000000,
        priority_flag: int = 0x00000000,
        schedule_delivery_time: str = "",
        validity_period: str = "",
        # xxxxxx01 SMSC Delivery Receipt requested where final delivery outcome is delivery success or failure
        # xxxx01xx SME Delivery Acknowledgement requested
        # xxx0xxxx No Intermediate notification requested
        # all other values reserved
        registered_delivery: int = 0b00000001,  # see section 5.2.17
        replace_if_present_flag: int = 0x00000000,
        sm_default_msg_id: int = 0x00000000,
    ) -> None:
        """
        Parameters:
            short_message: message to send to SMSC
            source_addr: the identifier(eg msisdn) of the message sender
            destination_addr: the identifier(eg msisdn) of the message recipient
            log_id: a unique identify of this request
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            smpp_command: any one of the SMSC commands eg submit_sm
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
            service_type:	Indicates the SMS Application service associated with the message
            source_addr_ton:	Type of Number of message originator.
            source_addr_npi:	Numbering Plan Identity of message originator.
            dest_addr_ton:	Type of Number for destination.
            dest_addr_npi:	Numbering Plan Identity of destination
            esm_class:	Indicates Message Mode & Message Type.
            protocol_id:	Protocol Identifier. Network specific field.
            priority_flag:	Designates the priority level of the message.
            schedule_delivery_time:	The short message is to be scheduled by the SMSC for delivery.
            validity_period:	The validity period of this message.
            registered_delivery:	Indicator to signify if an SMSC delivery receipt or an SME acknowledgement is required.
            replace_if_present_flag:	Flag indicating if submitted message should replace an existing message.
            sm_default_msg_id:	Indicates the short message to send from a list of predefined (‘canned’) short messages stored on the SMSC
        """
        self._validate_msg_type_args(
            short_message=short_message,
            source_addr=source_addr,
            destination_addr=destination_addr,
            log_id=log_id,
            version=version,
            hook_metadata=hook_metadata,
            service_type=service_type,
            source_addr_ton=source_addr_ton,
            source_addr_npi=source_addr_npi,
            dest_addr_ton=dest_addr_ton,
            dest_addr_npi=dest_addr_npi,
            esm_class=esm_class,
            protocol_id=protocol_id,
            priority_flag=priority_flag,
            schedule_delivery_time=schedule_delivery_time,
            validity_period=validity_period,
            registered_delivery=registered_delivery,
            replace_if_present_flag=replace_if_present_flag,
            sm_default_msg_id=sm_default_msg_id,
        )

        self.smpp_command: str = state.SmppCommand.SUBMIT_SM
        self.version = version

        self.short_message = short_message
        self.source_addr = source_addr
        self.destination_addr = destination_addr
        self.log_id = log_id
        self.hook_metadata = hook_metadata
        self.service_type = service_type
        self.source_addr_ton = source_addr_ton
        self.source_addr_npi = source_addr_npi
        self.dest_addr_ton = dest_addr_ton
        self.dest_addr_npi = dest_addr_npi
        self.esm_class = esm_class
        self.protocol_id = protocol_id
        self.priority_flag = priority_flag
        self.schedule_delivery_time = schedule_delivery_time
        self.validity_period = validity_period
        self.registered_delivery = registered_delivery
        self.replace_if_present_flag = replace_if_present_flag
        self.sm_default_msg_id = sm_default_msg_id

    @staticmethod
    def _validate_msg_type_args(
        short_message: str,
        source_addr: str,
        destination_addr: str,
        log_id: str,
        version: int,
        hook_metadata: str,
        service_type: str,
        source_addr_ton: int,
        source_addr_npi: int,
        dest_addr_ton: int,
        dest_addr_npi: int,
        esm_class: int,
        protocol_id: int,
        priority_flag: int,
        schedule_delivery_time: str,
        validity_period: str,
        registered_delivery: int,
        replace_if_present_flag: int,
        sm_default_msg_id: int,
    ) -> None:
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(short_message, str):
            raise ValueError(
                "`short_message` should be of type:: `str` You entered: {0}".format(
                    type(short_message)
                )
            )
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
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        if not isinstance(service_type, str):
            raise ValueError(
                "`service_type` should be of type:: `str` You entered: {0}".format(
                    type(service_type)
                )
            )
        if not isinstance(source_addr_ton, int):
            raise ValueError(
                "`source_addr_ton` should be of type:: `int` You entered: {0}".format(
                    type(source_addr_ton)
                )
            )
        if not isinstance(source_addr_npi, int):
            raise ValueError(
                "`source_addr_npi` should be of type:: `int` You entered: {0}".format(
                    type(source_addr_npi)
                )
            )
        if not isinstance(dest_addr_ton, int):
            raise ValueError(
                "`dest_addr_ton` should be of type:: `int` You entered: {0}".format(
                    type(dest_addr_ton)
                )
            )
        if not isinstance(dest_addr_npi, int):
            raise ValueError(
                "`dest_addr_npi` should be of type:: `int` You entered: {0}".format(
                    type(dest_addr_npi)
                )
            )
        if not isinstance(esm_class, int):
            raise ValueError(
                "`esm_class` should be of type:: `int` You entered: {0}".format(type(esm_class))
            )
        if not isinstance(protocol_id, int):
            raise ValueError(
                "`protocol_id` should be of type:: `int` You entered: {0}".format(type(protocol_id))
            )
        if not isinstance(priority_flag, int):
            raise ValueError(
                "`priority_flag` should be of type:: `int` You entered: {0}".format(
                    type(priority_flag)
                )
            )
        if not isinstance(schedule_delivery_time, str):
            raise ValueError(
                "`schedule_delivery_time` should be of type:: `str` You entered: {0}".format(
                    type(schedule_delivery_time)
                )
            )
        if not isinstance(validity_period, str):
            raise ValueError(
                "`validity_period` should be of type:: `str` You entered: {0}".format(
                    type(validity_period)
                )
            )
        if not isinstance(registered_delivery, int):
            raise ValueError(
                "`registered_delivery` should be of type:: `int` You entered: {0}".format(
                    type(registered_delivery)
                )
            )
        if not isinstance(replace_if_present_flag, int):
            raise ValueError(
                "`replace_if_present_flag` should be of type:: `int` You entered: {0}".format(
                    type(replace_if_present_flag)
                )
            )
        if not isinstance(sm_default_msg_id, int):
            raise ValueError(
                "`sm_default_msg_id` should be of type:: `int` You entered: {0}".format(
                    type(sm_default_msg_id)
                )
            )

    def to_json(self) -> str:
        _item = dict(
            smpp_command=self.smpp_command,
            version=self.version,
            short_message=self.short_message,
            source_addr=self.source_addr,
            destination_addr=self.destination_addr,
            log_id=self.log_id,
            hook_metadata=self.hook_metadata,
            service_type=self.service_type,
            source_addr_ton=self.source_addr_ton,
            source_addr_npi=self.source_addr_npi,
            dest_addr_ton=self.dest_addr_ton,
            dest_addr_npi=self.dest_addr_npi,
            esm_class=self.esm_class,
            protocol_id=self.protocol_id,
            priority_flag=self.priority_flag,
            schedule_delivery_time=self.schedule_delivery_time,
            validity_period=self.validity_period,
            registered_delivery=self.registered_delivery,
            replace_if_present_flag=self.replace_if_present_flag,
            sm_default_msg_id=self.sm_default_msg_id,
        )
        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> "SubmitSM":
        _in_dict = json.loads(json_message)
        return SubmitSM(**_in_dict)


class EnquireLinkResp(Message):
    def __init__(
        self,
        log_id: str,
        sequence_number: int,
        version: int = 1,
        smpp_command: str = state.SmppCommand.ENQUIRE_LINK_RESP,
        hook_metadata: str = "",
    ) -> None:
        """
        Parameters:
            log_id: a unique identify of this request
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            smpp_command: any one of the SMSC commands eg submit_sm
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
            sequence_number: SMPP sequence_number
        """
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(sequence_number, int):
            raise ValueError(
                "`sequence_number` should be of type:: `int` You entered: {0}".format(
                    type(sequence_number)
                )
            )
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(smpp_command, str):
            raise ValueError(
                "`smpp_command` should be of type:: `str` You entered: {0}".format(
                    type(smpp_command)
                )
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        self.log_id = log_id
        self.sequence_number = sequence_number
        self.version = version
        self.smpp_command = state.SmppCommand.ENQUIRE_LINK_RESP
        self.hook_metadata = hook_metadata

    def to_json(self) -> str:
        _item = dict(
            smpp_command=self.smpp_command,
            version=self.version,
            log_id=self.log_id,
            sequence_number=self.sequence_number,
            hook_metadata=self.hook_metadata,
        )
        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> "EnquireLinkResp":
        _in_dict = json.loads(json_message)
        return EnquireLinkResp(**_in_dict)


class DeliverSmResp(Message):
    def __init__(
        self,
        log_id: str,
        message_id: str,
        sequence_number: int,
        version: int = 1,
        smpp_command: str = state.SmppCommand.DELIVER_SM_RESP,
        hook_metadata: str = "",
    ) -> None:
        """
        Parameters:
            log_id: a unique identify of this request
            version: This indicates the current version of the naz message protocol.
                     This version will enable naz to be able to evolve in future; a future version of `naz` may ship with a different message protocol.
            smpp_command: any one of the SMSC commands eg submit_sm
            hook_metadata: a string that to will later on be passed to `naz.Client.hook`. Your application can use it for correlation.
            message_id: id of this message
            sequence_number: SMPP sequence_number
        """
        if not isinstance(log_id, str):
            raise ValueError(
                "`log_id` should be of type:: `str` You entered: {0}".format(type(log_id))
            )
        if not isinstance(message_id, str):
            raise ValueError(
                "`message_id` should be of type:: `str` You entered: {0}".format(type(message_id))
            )
        if not isinstance(sequence_number, int):
            raise ValueError(
                "`sequence_number` should be of type:: `int` You entered: {0}".format(
                    type(sequence_number)
                )
            )
        if not isinstance(version, int):
            raise ValueError(
                "`version` should be of type:: `int` You entered: {0}".format(type(version))
            )
        if version != NAZ_MESSAGE_PROTOCOL_VERSION:
            raise ValueError(
                "`naz` currently only supports naz protocol version {0}".format(
                    NAZ_MESSAGE_PROTOCOL_VERSION
                )
            )
        if not isinstance(smpp_command, str):
            raise ValueError(
                "`smpp_command` should be of type:: `str` You entered: {0}".format(
                    type(smpp_command)
                )
            )
        if not isinstance(hook_metadata, str):
            raise ValueError(
                "`hook_metadata` should be of type:: `str` You entered: {0}".format(
                    type(hook_metadata)
                )
            )
        self.log_id = log_id
        self.version = version
        self.smpp_command = state.SmppCommand.DELIVER_SM_RESP
        self.message_id = message_id
        self.sequence_number = sequence_number
        self.hook_metadata = hook_metadata

    def to_json(self) -> str:
        _item = dict(
            smpp_command=self.smpp_command,
            version=self.version,
            log_id=self.log_id,
            message_id=self.message_id,
            sequence_number=self.sequence_number,
            hook_metadata=self.hook_metadata,
        )
        return json.dumps(_item)

    @staticmethod
    def from_json(json_message: str) -> "DeliverSmResp":
        _in_dict = json.loads(json_message)
        return DeliverSmResp(**_in_dict)


def json_to_Message(json_message: str) -> Message:
    """
    Utility function to deserialize the message protocol from json.
    You can use this method if you would like to return the `Message` from a broker like redis/rabbitmq/postgres etc.

    Parameters:
        json_message: `naz.protocol.Message` in json format.
    """
    _item = json.loads(json_message)
    smpp_command = _item["smpp_command"]
    if smpp_command == state.SmppCommand.SUBMIT_SM:
        return SubmitSM.from_json(json_message=json_message)
    elif smpp_command == state.SmppCommand.ENQUIRE_LINK_RESP:
        return EnquireLinkResp.from_json(json_message=json_message)
    elif smpp_command == state.SmppCommand.DELIVER_SM_RESP:
        return DeliverSmResp.from_json(json_message=json_message)
    else:
        raise NotImplementedError(
            "The `from_json` method for smpp_command: `{0}` has not been implemented.".format(
                smpp_command
            )
        )

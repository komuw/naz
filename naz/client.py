import struct
import random
import string
import typing
import asyncio
import logging

from . import q
from . import hooks
from . import logger
from . import nazcodec
from . import sequence
from . import throttle
from . import correlater
from . import ratelimiter

from .state import SmppSessionState, SmppCommand, SmppCommandStatus, SmppDataCoding


class Client:
    """
    The SMPP client that will interact with SMSC/server.

    Example declaration:

    .. code-block:: python

        import os
        import asyncio
        import naz
        loop = asyncio.get_event_loop()
        outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000, loop=loop)
        client = naz.Client(
                async_loop=loop,
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                outboundqueue=outboundqueue,
            )
    """

    def __init__(
        self,
        async_loop: asyncio.events.AbstractEventLoop,
        smsc_host: str,
        smsc_port: int,
        system_id: str,
        password: str,
        outboundqueue: q.BaseOutboundQueue,
        client_id=None,
        system_type: str = "",
        addr_ton: int = 0,
        addr_npi: int = 0,
        address_range: str = "",
        encoding: str = "gsm0338",
        interface_version: int = 34,
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
        enquire_link_interval: int = 300,
        log_handler=None,
        loglevel: str = "DEBUG",
        log_metadata=None,
        codec_class=None,
        codec_errors_level: str = "strict",
        rateLimiter=None,
        hook=None,
        sequence_generator=None,
        throttle_handler=None,
        correlation_handler=None,
    ) -> None:
        """
        Parameters:
            async_loop: asyncio event loop.
            smsc_host:	the IP address(or domain name) of the SMSC gateway/server
            smsc_port:	the port at which SMSC is listening on
            system_id:	Identifies the ESME system requesting to bind as a transceiver with the SMSC.
            password:	The password to be used by the SMSC to authenticate the ESME requesting to bind.
            system_type:	Identifies the type of ESME system requesting to bind with the SMSC.
            addr_ton:	Type of Number of the ESME address.
            addr_npi:	Numbering Plan Indicator (NPI) for ESME address(es) served via this SMPP transceiver session
            address_range:	A single ESME address or a range of ESME addresses served via this SMPP transceiver session.
            interface_version:	Indicates the version of the SMPP protocol supported by the ESME.
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
            encoding:	encoding1 used to encode messages been sent to SMSC
            sequence_generator:	python class instance used to generate sequence_numbers
            outboundqueue:	python class instance implementing some queueing mechanism. \
                messages to be sent to SMSC are queued using the said mechanism before been sent
            client_id:	a unique string identifying a naz client class instance
            log_handler: python class instance to be used for logging
            loglevel:	the level at which to log
            log_metadata: metadata that will be included in all log statements
            codec_class: python class instance to be used to encode/decode messages
            codec_errors_level:	same meaning as the errors argument to pythons' encode method as defined here
            enquire_link_interval:	time in seconds to wait before sending an enquire_link request to SMSC to check on its status
            rateLimiter: python class instance implementing rate limitation
            hook: python class instance implemeting functionality/hooks to be called by naz \
                just before sending request to SMSC and just after getting response from SMSC
            throttle_handler: python class instance implementing functionality of what todo when naz starts getting throttled responses from SMSC
            correlation_handler: A python class instance that naz uses to store relations between \
                SMPP sequence numbers and user applications' log_id's and/or hook_metadata.
        """
        if loglevel.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                """loglevel should be one of; 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'. not {0}""".format(
                    loglevel
                )
            )
        elif not isinstance(log_metadata, (type(None), dict)):
            raise ValueError(
                """log_metadata should be of type:: None or dict. You entered {0}""".format(
                    type(log_metadata)
                )
            )

        # this allows people to pass in their own event loop eg uvloop.
        self.async_loop = async_loop
        self.smsc_host = smsc_host
        self.smsc_port = smsc_port
        self.system_id = system_id
        self.password = password
        self.outboundqueue = outboundqueue
        self.client_id = client_id
        if not self.client_id:
            self.client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=17))
        self.system_type = system_type
        self.interface_version = interface_version
        self.addr_ton = addr_ton
        self.addr_npi = addr_npi
        self.address_range = address_range
        self.encoding = encoding

        self.sequence_generator = sequence_generator
        if not self.sequence_generator:
            self.sequence_generator = sequence.SimpleSequenceGenerator()

        self.max_sequence_number = 0x7FFFFFFF
        self.loglevel = loglevel.upper()
        self.log_metadata = log_metadata
        if not self.log_metadata:
            self.log_metadata = {}
        self.log_metadata.update(
            {"smsc_host": self.smsc_host, "system_id": system_id, "client_id": self.client_id}
        )

        self.codec_errors_level = codec_errors_level
        self.codec_class = codec_class
        if not self.codec_class:
            self.codec_class = nazcodec.SimpleNazCodec()

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
        self.enquire_link_interval = enquire_link_interval

        # see section 5.1.2.1 of smpp ver 3.4 spec document
        self.command_ids = {
            SmppCommand.BIND_TRANSCEIVER: 0x00000009,
            SmppCommand.BIND_TRANSCEIVER_RESP: 0x80000009,
            SmppCommand.UNBIND: 0x00000006,
            SmppCommand.UNBIND_RESP: 0x80000006,
            SmppCommand.SUBMIT_SM: 0x00000004,
            SmppCommand.SUBMIT_SM_RESP: 0x80000004,
            SmppCommand.DELIVER_SM: 0x00000005,
            SmppCommand.DELIVER_SM_RESP: 0x80000005,
            SmppCommand.ENQUIRE_LINK: 0x00000015,
            SmppCommand.ENQUIRE_LINK_RESP: 0x80000015,
            SmppCommand.GENERIC_NACK: 0x80000000,
        }

        self.data_coding = self._find_data_coding(self.encoding)

        self.reader: typing.Any = None
        self.writer: typing.Any = None

        # NB: currently, naz only uses to log levels; INFO and EXCEPTION
        self.logger = log_handler
        if not self.logger:
            self.logger = logger.SimpleBaseLogger("naz.client")
        self.logger.bind(loglevel=self.loglevel, log_metadata=self.log_metadata)
        self._sanity_check_logger()

        self.rateLimiter = rateLimiter
        if not self.rateLimiter:
            self.rateLimiter = ratelimiter.SimpleRateLimiter(logger=self.logger)

        self.hook = hook
        if not self.hook:
            self.hook = hooks.SimpleHook(logger=self.logger)

        self.throttle_handler = throttle_handler
        if not self.throttle_handler:
            self.throttle_handler = throttle.SimpleThrottleHandler(logger=self.logger)

        # class storing SMPP sequence_number and their corresponding log_id and/or hook_metadata
        # this will be used to track different pdu's and user generated log_id
        self.correlation_handler = correlation_handler
        if not self.correlation_handler:
            self.correlation_handler = correlater.SimpleCorrelater()

        # the messages that are published to a queue by either naz
        # or user application should be versioned.
        # This version will enable naz to be able to evolve in future;
        # eg a future version of naz could add/remove the number of required items in a message.
        # This is a bit similar to: http://docs.celeryproject.org/en/latest/internals/protocol.html
        self.naz_message_protocol_version = "1"

        self.current_session_state = SmppSessionState.CLOSED

    def _sanity_check_logger(self):
        """
        called when instantiating the Client just to make sure the supplied
        logger can log.
        """
        try:
            self.logger.log(logging.DEBUG, {"event": "sanity_check_logger"})
        except Exception as e:
            raise e

    def _log(self, level, log_data):
        # if the supplied logger is unable to log; we move on
        try:
            self.logger.log(level, log_data)
        except Exception:
            pass

    @staticmethod
    def _find_data_coding(encoding):
        for key, val in SmppDataCoding.__dict__.items():
            if not key.startswith("__"):
                if encoding == val.code:
                    return val.value
        raise ValueError("That encoding:{0} is not recognised.".format(encoding))

    def _search_by_command_id_code(self, command_id_code):
        for key, val in self.command_ids.items():
            if val == command_id_code:
                return key
        return None

    @staticmethod
    def _search_by_command_status_value(command_status_value):
        # TODO: find a cheaper(better) way of doing this
        for key, val in SmppCommandStatus.__dict__.items():
            if not key.startswith("__"):
                if command_status_value == val.value:
                    return val
        return None

    @staticmethod
    def _retry_after(current_retries):
        """
        retries will happen in this sequence;
        1min, 2min, 4min, 8min, 16min, 32min, 16min, 16min, 16min ...
        """
        # TODO:
        # 1. give users ability to bring their own retry algorithms.
        # 2. add jitter
        if current_retries < 0:
            current_retries = 0
        if current_retries >= 6:
            return 60 * 16  # 16 minutes
        else:
            return 60 * (1 * (2 ** current_retries))

    async def connect(
        self
    ) -> typing.Tuple[asyncio.streams.StreamReader, asyncio.streams.StreamWriter]:
        """
        make a network connection to SMSC server.
        """
        self._log(logging.INFO, {"event": "naz.Client.connect", "stage": "start"})
        reader, writer = await asyncio.open_connection(
            self.smsc_host, self.smsc_port, loop=self.async_loop
        )
        self.reader: asyncio.streams.StreamReader = reader
        self.writer: asyncio.streams.StreamWriter = writer
        self._log(logging.INFO, {"event": "naz.Client.connect", "stage": "end"})
        self.current_session_state = SmppSessionState.OPEN
        return reader, writer

    async def tranceiver_bind(self) -> None:
        """
        send a BIND_RECEIVER pdu to SMSC.
        """
        smpp_command = SmppCommand.BIND_TRANSCEIVER
        log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.tranceiver_bind",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )
        # body
        body = b""
        body = (
            body
            + self.codec_class.encode(self.system_id, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + self.codec_class.encode(self.password, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + self.codec_class.encode(self.system_type, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + struct.pack(">I", self.interface_version)
            + struct.pack(">I", self.addr_ton)
            + struct.pack(">I", self.addr_npi)
            + self.codec_class.encode(self.address_range, self.encoding, self.codec_errors_level)
            + chr(0).encode()
        )

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        # the status for success see section 5.1.3
        command_status = SmppCommandStatus.ESME_ROK.value
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.tranceiver_bind",
                    "stage": "end",
                    "error": str(e),
                    "smpp_command": smpp_command,
                },
            )

        if sequence_number > self.max_sequence_number:
            # prevent third party sequence_generators from ruining our party
            raise ValueError(
                "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                    sequence_number, self.max_sequence_number
                )
            )

        # associate sequence_number with log_id.
        # this will enable us to also associate responses and thus enhancing traceability of all workflows
        try:
            await self.correlation_handler.put(
                sequence_number=sequence_number, log_id=log_id, hook_metadata=""
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.tranceiver_bind",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "correlater put error",
                    "error": str(e),
                },
            )

        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)
        full_pdu = header + body
        await self.send_data(smpp_command=smpp_command, msg=full_pdu, log_id=log_id)
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.tranceiver_bind",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

    async def enquire_link(self, TESTING: bool = False) -> typing.Union[bytes, None]:
        """
        send an ENQUIRE_LINK pdu to SMSC.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        smpp_command = SmppCommand.ENQUIRE_LINK
        while True:
            if self.current_session_state != SmppSessionState.BOUND_TRX:
                # you can only send enquire_link request when session state is BOUND_TRX
                await asyncio.sleep(self.enquire_link_interval)

            log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
            self._log(
                logging.INFO,
                {
                    "event": "naz.Client.enquire_link",
                    "stage": "start",
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
            # body
            body = b""

            # header
            command_length = 16 + len(body)  # 16 is for headers
            command_id = self.command_ids[smpp_command]
            command_status = 0x00000000  # not used for `enquire_link`
            try:
                sequence_number = self.sequence_generator.next_sequence()
            except Exception as e:
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.enquire_link",
                        "stage": "end",
                        "error": str(e),
                        "log_id": log_id,
                        "smpp_command": smpp_command,
                    },
                )
            if sequence_number > self.max_sequence_number:
                # prevent third party sequence_generators from ruining our party
                raise ValueError(
                    "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                        sequence_number, self.max_sequence_number
                    )
                )

            try:
                await self.correlation_handler.put(
                    sequence_number=sequence_number, log_id=log_id, hook_metadata=""
                )
            except Exception as e:
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.enquire_link",
                        "stage": "end",
                        "smpp_command": smpp_command,
                        "log_id": log_id,
                        "state": "correlater put error",
                        "error": str(e),
                    },
                )

            header = struct.pack(
                ">IIII", command_length, command_id, command_status, sequence_number
            )
            full_pdu = header + body
            # dont queue enquire_link in SimpleOutboundQueue since we dont want it to be behind 10k msgs etc
            await self.send_data(smpp_command=smpp_command, msg=full_pdu, log_id=log_id)
            self._log(
                logging.INFO,
                {
                    "event": "naz.Client.enquire_link",
                    "stage": "end",
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
            if TESTING:
                return full_pdu
            await asyncio.sleep(self.enquire_link_interval)

    async def enquire_link_resp(self, sequence_number: int) -> None:
        """
        send an ENQUIRE_LINK_RESP pdu to SMSC.

        Parameters:
            sequence_number: SMPP sequence_number
        """
        smpp_command = SmppCommand.ENQUIRE_LINK_RESP
        log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.enquire_link_resp",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

        # body
        body = b""

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = SmppCommandStatus.ESME_ROK.value
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        item_to_enqueue = {
            "version": self.naz_message_protocol_version,
            "log_id": log_id,
            "pdu": full_pdu,
            "smpp_command": smpp_command,
        }
        try:
            await self.outboundqueue.enqueue(item_to_enqueue)
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.enquire_link_resp",
                    "stage": "end",
                    "error": str(e),
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.enquire_link_resp",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

    async def unbind_resp(self, sequence_number: int) -> None:
        """
        send an UNBIND_RESP pdu to SMSC.

        Parameters:
            sequence_number: SMPP sequence_number
        """
        smpp_command = SmppCommand.UNBIND_RESP
        log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.unbind_resp",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

        # body
        body = b""

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = SmppCommandStatus.ESME_ROK.value
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        # dont queue unbind_resp in SimpleOutboundQueue since we dont want it to be behind 10k msgs etc
        await self.send_data(smpp_command=smpp_command, msg=full_pdu, log_id=log_id)
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.unbind_resp",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

    async def deliver_sm_resp(self, sequence_number: int) -> None:
        """
        send a DELIVER_SM_RESP pdu to SMSC.

        Parameters:
            sequence_number: SMPP sequence_number
        """
        smpp_command = SmppCommand.DELIVER_SM_RESP
        log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.deliver_sm_resp",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )
        # body
        body = b""
        message_id = ""
        body = (
            body
            + self.codec_class.encode(message_id, self.encoding, self.codec_errors_level)
            + chr(0).encode()
        )

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = SmppCommandStatus.ESME_ROK.value
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        item_to_enqueue = {
            "version": self.naz_message_protocol_version,
            "log_id": log_id,
            "pdu": full_pdu,
            "smpp_command": smpp_command,
        }
        try:
            await self.outboundqueue.enqueue(item_to_enqueue)
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.deliver_sm_resp",
                    "stage": "end",
                    "error": str(e),
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )

        self._log(
            logging.INFO,
            {
                "event": "naz.Client.deliver_sm_resp",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

    # this method just enqueues a submit_sm msg to queue
    async def submit_sm(
        self, short_message: str, log_id: str, source_addr: str, destination_addr: str
    ) -> None:
        """
        enqueues a SUBMIT_SM pdu to :attr:`outboundqueue <Client.outboundqueue>`
        That PDU will later on be sent to SMSC.

        Parameters:
            short_message: message to send to SMSC
            log_id: a unique identify of this request
            source_addr: the identifier(eg msisdn) of the message sender
            destination_addr: the identifier(eg msisdn) of the message recipient
        """
        # HEADER::
        # submit_sm has the following pdu header:
        # command_length, int, 4octet
        # command_id, int, 4octet. `submit_sm`
        # command_status, int, 4octet. Not used. Set to NULL
        # sequence_number, int, 4octet.  The associated submit_sm_resp PDU will echo this sequence number.

        # BODY::
        # submit_sm has the following pdu body. NB: They SHOULD be put in the body in the ORDER presented here.
        # service_type, c-octet str, max 6octet. eg NULL, "USSD", "CMT" etc
        # source_addr_ton, int , 1octet,
        # source_addr_npi, int, 1octet
        # source_addr, c-octet str, max 21octet. eg; This is usually the senders phone Number
        # dest_addr_ton, int, 1octet
        # dest_addr_npi, int, 1octet
        # destination_addr,  C-Octet String, max 21 octet. eg; This is usually the recipients phone Number
        # esm_class, int, 1octet
        # protocol_id, int, 1octet
        # priority_flag, int, 1octet
        # schedule_delivery_time, c-octet str, 1 or 17 octets. NULL for immediate message delivery.
        # validity_period, c-octet str, 1 or 17 octets.  NULL for SMSC default.
        # registered_delivery, int, 1octet
        # replace_if_present_flag, int, 1octet
        # data_coding, int, 1octet. Defines the encoding scheme of the short message user data. Bits 7 6 5 4 3 2 1 0
        # sm_default_msg_id, int, 1octet. SMSC index of a pre-defined(`canned`) message.  If not using an SMSC canned message, set to NULL
        # sm_length, int, 1octet. Length in octets of the `short_message`.
        # short_message, Octet-String(NOT c-octet str), 0-254 octets.
        # NB: 1. Applications which need to send messages longer than 254 octets should use the `message_payload` optional parameter.
        #        In this case the `sm_length` field should be set to zero
        #        u cant use both `short_message` and `message_payload`
        #     2. Octet String - A series of octets, not necessarily NULL terminated.

        smpp_command = SmppCommand.SUBMIT_SM
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.submit_sm",
                "stage": "start",
                "log_id": log_id,
                "short_message": short_message,
                "source_addr": source_addr,
                "destination_addr": destination_addr,
                "smpp_command": smpp_command,
            },
        )
        item_to_enqueue = {
            "version": self.naz_message_protocol_version,
            "smpp_command": smpp_command,
            "short_message": short_message,
            "log_id": log_id,
            "source_addr": source_addr,
            "destination_addr": destination_addr,
        }
        try:
            await self.outboundqueue.enqueue(item_to_enqueue)
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.submit_sm",
                    "stage": "end",
                    "error": str(e),
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.submit_sm",
                "stage": "end",
                "log_id": log_id,
                "short_message": short_message,
                "source_addr": source_addr,
                "destination_addr": destination_addr,
                "smpp_command": smpp_command,
            },
        )

    async def build_submit_sm_pdu(
        self, short_message, log_id, hook_metadata, source_addr, destination_addr
    ) -> bytes:
        """
        builds a SUBMIT_SM pdu.

        Parameters:
            short_message: message to send to SMSC
            log_id: a unique identify of this request
            hook_metadata: additional metadata that you would like to be passed on to hooks
            source_addr: the identifier(eg msisdn) of the message sender
            destination_addr: the identifier(eg msisdn) of the message recipient
        """
        smpp_command = SmppCommand.SUBMIT_SM
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.build_submit_sm_pdu",
                "stage": "start",
                "log_id": log_id,
                "short_message": short_message,
                "source_addr": source_addr,
                "destination_addr": destination_addr,
                "smpp_command": smpp_command,
            },
        )
        encoded_short_message = self.codec_class.encode(
            short_message, self.encoding, self.codec_errors_level
        )
        sm_length = len(encoded_short_message)

        # body
        body = b""
        body = (
            body
            + self.codec_class.encode(self.service_type, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + struct.pack(">B", self.source_addr_ton)
            + struct.pack(">B", self.source_addr_npi)
            + self.codec_class.encode(source_addr, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + struct.pack(">B", self.dest_addr_ton)
            + struct.pack(">B", self.dest_addr_npi)
            + self.codec_class.encode(destination_addr, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + struct.pack(">B", self.esm_class)
            + struct.pack(">B", self.protocol_id)
            + struct.pack(">B", self.priority_flag)
            + self.codec_class.encode(
                self.schedule_delivery_time, self.encoding, self.codec_errors_level
            )
            + chr(0).encode()
            + self.codec_class.encode(self.validity_period, self.encoding, self.codec_errors_level)
            + chr(0).encode()
            + struct.pack(">B", self.registered_delivery)
            + struct.pack(">B", self.replace_if_present_flag)
            + struct.pack(">B", self.data_coding)
            + struct.pack(">B", self.sm_default_msg_id)
            + struct.pack(">B", sm_length)
            + self.codec_class.encode(short_message, self.encoding, self.codec_errors_level)
        )

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        # the status for success see section 5.1.3
        command_status = 0x00000000  # not used for `submit_sm`
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.build_submit_sm_pdu",
                    "stage": "end",
                    "error": str(e),
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
        if sequence_number > self.max_sequence_number:
            # prevent third party sequence_generators from ruining our party
            raise ValueError(
                "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                    sequence_number, self.max_sequence_number
                )
            )

        try:
            await self.correlation_handler.put(
                sequence_number=sequence_number, log_id=log_id, hook_metadata=hook_metadata
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.build_submit_sm_pdu",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "correlater put error",
                    "error": str(e),
                },
            )

        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)
        full_pdu = header + body
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.build_submit_sm_pdu",
                "stage": "end",
                "log_id": log_id,
                "short_message": short_message,
                "source_addr": source_addr,
                "destination_addr": destination_addr,
                "smpp_command": smpp_command,
            },
        )
        return full_pdu

    async def send_data(
        self, smpp_command: str, msg: bytes, log_id: str, hook_metadata: str = ""
    ) -> None:
        """
        Sends PDU's to SMSC through/over a network connection(down the wire).
        This method does not block; it buffers the data and arranges for it to be sent out asynchronously.
        It also accts as a flow control method that interacts with the IO write buffer.

        Parameters:
            smpp_command: type of PDU been sent. eg bind_transceiver
            msg: PDU to be sent to SMSC over the network connection.
            log_id: a unique identify of this request
            hook_metadata: additional metadata that you would like to be passed on to hooks
        """
        # todo: look at `set_write_buffer_limits` and `get_write_buffer_limits` methods
        # print("get_write_buffer_limits:", writer.transport.get_write_buffer_limits())

        log_msg = ""
        try:
            log_msg = self.codec_class.decode(msg, self.encoding, self.codec_errors_level)
            # do not log password, redact it from logs.
            if self.password in log_msg:
                log_msg = log_msg.replace(self.password, "{REDACTED}")
        except Exception:
            pass
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.send_data",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "msg": log_msg,
            },
        )

        # check session state to see if we can send messages.
        # see section 2.3 of SMPP spec document v3.4
        if self.current_session_state == SmppSessionState.CLOSED:
            error_msg = "smpp_command: {0} cannot be sent to SMSC when the client session state is: {1}".format(
                smpp_command, self.current_session_state
            )
            self._log(
                logging.INFO,
                {
                    "event": "naz.Client.send_data",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "msg": log_msg,
                    "current_session_state": self.current_session_state,
                    "error": error_msg,
                },
            )
            raise ValueError(error_msg)
        elif self.current_session_state == SmppSessionState.OPEN and smpp_command not in [
            "bind_transmitter",
            "bind_receiver",
            "bind_transceiver",
        ]:
            # only the smpp_command's listed above are allowed by SMPP spec to be sent
            # if current_session_state == SmppSessionState.OPEN
            error_msg = "smpp_command: {0} cannot be sent to SMSC when the client session state is: {1}".format(
                smpp_command, self.current_session_state
            )
            self._log(
                logging.INFO,
                {
                    "event": "naz.Client.send_data",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "msg": log_msg,
                    "current_session_state": self.current_session_state,
                    "error": error_msg,
                },
            )
            raise ValueError(error_msg)

        if isinstance(msg, str):
            msg = self.codec_class.encode(msg, self.encoding, self.codec_errors_level)

        # call user's hook for requests
        try:
            await self.hook.request(
                smpp_command=smpp_command, log_id=log_id, hook_metadata=hook_metadata
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.send_data",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "request hook error",
                    "error": str(e),
                },
            )

        # We use writer.drain() which is a flow control method that interacts with the IO write buffer.
        # When the size of the buffer reaches the high watermark,
        # drain blocks until the size of the buffer is drained down to the low watermark and writing can be resumed.
        # When there is nothing to wait for, the drain() returns immediately.
        # ref: https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.drain
        self.writer.write(msg)
        await self.writer.drain()
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.send_data",
                "stage": "end",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "msg": log_msg,
            },
        )

    async def send_forever(
        self, TESTING: bool = False
    ) -> typing.Union[str, typing.Dict[typing.Any, typing.Any]]:
        """
        In loop; dequeues items from the :attr:`outboundqueue <Client.outboundqueue>` and sends them to SMSC.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        retry_count = 0
        while True:
            self._log(logging.INFO, {"event": "naz.Client.send_forever", "stage": "start"})

            # TODO: there are so many try-except classes in this func.
            # do something about that.
            try:
                # check with throttle handler
                send_request = await self.throttle_handler.allow_request()
            except Exception as e:
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.send_forever",
                        "stage": "end",
                        "state": "send_forever error",
                        "error": str(e),
                    },
                )
                continue
            if send_request:
                try:
                    # rate limit ourselves
                    await self.rateLimiter.limit()
                except Exception as e:
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.send_forever",
                            "stage": "end",
                            "state": "send_forever error",
                            "error": str(e),
                        },
                    )
                    continue

                try:
                    item_to_dequeue = await self.outboundqueue.dequeue()
                except Exception as e:
                    retry_count += 1
                    poll_queue_interval = self._retry_after(retry_count)
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.send_forever",
                            "stage": "end",
                            "state": "send_forever error. sleeping for {0}minutes".format(
                                poll_queue_interval / 60
                            ),
                            "retry_count": retry_count,
                            "error": str(e),
                        },
                    )
                    await asyncio.sleep(poll_queue_interval)
                    continue
                # we didn't fail to dequeue a message
                retry_count = 0
                try:
                    log_id = item_to_dequeue["log_id"]
                    item_to_dequeue["version"]  # version is a required field
                    smpp_command = item_to_dequeue["smpp_command"]
                    hook_metadata = item_to_dequeue.get("hook_metadata", "")
                    if smpp_command == SmppCommand.SUBMIT_SM:
                        short_message = item_to_dequeue["short_message"]
                        source_addr = item_to_dequeue["source_addr"]
                        destination_addr = item_to_dequeue["destination_addr"]
                        full_pdu = await self.build_submit_sm_pdu(
                            short_message, log_id, hook_metadata, source_addr, destination_addr
                        )
                    else:
                        full_pdu = item_to_dequeue["pdu"]
                except KeyError as e:
                    e = KeyError(
                        "enqueued message/object is missing required field:{}".format(str(e))
                    )
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.send_forever",
                            "stage": "end",
                            "state": "send_forever error",
                            "error": str(e),
                        },
                    )
                    continue

                await self.send_data(
                    smpp_command=smpp_command,
                    msg=full_pdu,
                    log_id=log_id,
                    hook_metadata=hook_metadata,
                )
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.send_forever",
                        "stage": "end",
                        "log_id": log_id,
                        "smpp_command": smpp_command,
                        "send_request": send_request,
                    },
                )
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return item_to_dequeue
            else:
                # throttle_handler didn't allow us to send request.
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.send_forever",
                        "stage": "end",
                        "send_request": send_request,
                    },
                )
                try:
                    await asyncio.sleep(await self.throttle_handler.throttle_delay())
                except Exception as e:
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.send_forever",
                            "stage": "end",
                            "state": "send_forever error",
                            "error": str(e),
                        },
                    )
                    continue
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return {"throttle_handler_denied_request": "throttle_handler_denied_request"}
                continue

    async def receive_data(self, TESTING: bool = False) -> typing.Union[bytes, None]:
        """
        In loop; read bytes from the network connected to SMSC and hand them over to the :func:`throparserttled <Client.parse_response_pdu>`.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        retry_count = 0
        while True:
            self._log(logging.INFO, {"event": "naz.Client.receive_data", "stage": "start"})
            # todo: look at `pause_reading` and `resume_reading` methods
            command_length_header_data = await self.reader.read(4)
            if command_length_header_data == b"":
                retry_count += 1
                poll_read_interval = self._retry_after(retry_count)
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.receive_data",
                        "stage": "start",
                        "state": "no data received from SMSC. sleeping for {0}minutes".format(
                            poll_read_interval / 60
                        ),
                        "retry_count": retry_count,
                    },
                )
                await asyncio.sleep(poll_read_interval)
                continue
            else:
                # we didn't fail to read from SMSC
                retry_count = 0

            total_pdu_length = struct.unpack(">I", command_length_header_data)[0]

            MSGLEN = total_pdu_length - 4
            chunks = []
            bytes_recd = 0
            while bytes_recd < MSGLEN:
                chunk = await self.reader.read(min(MSGLEN - bytes_recd, 2048))
                if chunk == b"":
                    err = RuntimeError("socket connection broken")
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.receive_data",
                            "stage": "end",
                            "state": "socket connection broken",
                            "error": str(err),
                        },
                    )
                    raise err
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            full_pdu_data = command_length_header_data + b"".join(chunks)
            await self.parse_response_pdu(full_pdu_data)
            self._log(logging.INFO, {"event": "naz.Client.receive_data", "stage": "end"})
            if TESTING:
                # offer escape hatch for tests to come out of endless loop
                return full_pdu_data

    async def parse_response_pdu(self, pdu: bytes) -> None:
        """
        Take the bytes that have been read from network and parse them into their corresponding PDU.
        The resulting PDU is then handed over to :func:`speficic_handlers <Client.speficic_handlers>`

        Parameters:
            pdu: PDU in bytes, that have been read from network
        """
        self._log(logging.INFO, {"event": "naz.Client.parse_response_pdu", "stage": "start"})

        header_data = pdu[:16]
        command_id_header_data = header_data[4:8]
        command_status_header_data = header_data[8:12]
        sequence_number_header_data = header_data[12:16]

        command_id = struct.unpack(">I", command_id_header_data)[0]
        command_status = struct.unpack(">I", command_status_header_data)[0]
        sequence_number = struct.unpack(">I", sequence_number_header_data)[0]

        # get associated user supplied log_id if any
        try:
            log_id, hook_metadata = await self.correlation_handler.get(
                sequence_number=sequence_number
            )
        except Exception as e:
            log_id, hook_metadata = "", ""
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.parse_response_pdu",
                    "stage": "start",
                    "log_id": log_id,
                    "state": "correlater get error",
                    "error": str(e),
                },
            )

        smpp_command = self._search_by_command_id_code(command_id)
        if not smpp_command:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.parse_response_pdu",
                    "stage": "end",
                    "log_id": log_id,
                    "state": "command_id:{0} is unknown.".format(command_id),
                },
            )
            raise ValueError("command_id:{0} is unknown.".format(command_id))

        await self.speficic_handlers(
            smpp_command=smpp_command,
            command_status_value=command_status,
            sequence_number=sequence_number,
            log_id=log_id,
            hook_metadata=hook_metadata,
        )
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.parse_response_pdu",
                "stage": "end",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "command_status": command_status,
            },
        )

    async def speficic_handlers(
        self,
        smpp_command: str,
        command_status_value: int,
        sequence_number: int,
        log_id: str,
        hook_metadata: str,
    ) -> None:
        """
        This routes the various different SMPP PDU to their respective handlers.

        Parameters:
            smpp_command: type of PDU been sent. eg bind_transceiver
            command_status_value: the response code from SMSC for a specific PDU
            sequence_number: SMPP sequence_number
            log_id: a unique identify of this request
            hook_metadata: additional metadata that you would like to be passed on to hooks
        """
        commandStatus = self._search_by_command_status_value(
            command_status_value=command_status_value
        )
        if not commandStatus:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.speficic_handlers",
                    "stage": "start",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "error": "command_status:{0} is unknown.".format(command_status_value),
                },
            )
        elif commandStatus.value != SmppCommandStatus.ESME_ROK.value:
            # we got an error from SMSC
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.speficic_handlers",
                    "stage": "start",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "command_status": commandStatus.value,
                    "state": commandStatus.description,
                },
            )
        else:
            self._log(
                logging.INFO,
                {
                    "event": "naz.Client.speficic_handlers",
                    "stage": "start",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "command_status": commandStatus.value,
                    "state": commandStatus.description,
                },
            )

        try:
            # call throttling handler
            if commandStatus.value == SmppCommandStatus.ESME_ROK.value:
                await self.throttle_handler.not_throttled()
            elif commandStatus.value == SmppCommandStatus.ESME_RTHROTTLED.value:
                await self.throttle_handler.throttled()
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.speficic_handlers",
                    "stage": "end",
                    "error": str(e),
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": commandStatus.description,
                },
            )

        if smpp_command in [
            SmppCommand.BIND_TRANSCEIVER,
            SmppCommand.UNBIND_RESP,
            SmppCommand.SUBMIT_SM,  # We dont expect SMSC to send `submit_sm` to us.
            SmppCommand.DELIVER_SM_RESP,
            # we will never send a deliver_sm request to SMSC, which means we never
            # have to handle deliver_sm_resp
            SmppCommand.ENQUIRE_LINK_RESP,
            SmppCommand.GENERIC_NACK,  # we can ignore this
        ]:
            # we never have to handle this
            pass
        elif smpp_command == SmppCommand.BIND_TRANSCEIVER_RESP:
            # the body of `bind_transceiver_resp` only has `system_id` which is a
            # C-Octet String of variable length upto 16 octets
            if commandStatus.value == SmppCommandStatus.ESME_ROK.value:
                self.current_session_state = SmppSessionState.BOUND_TRX
        elif smpp_command == SmppCommand.UNBIND:
            # we need to handle this since we need to send unbind_resp
            # it has no body
            await self.unbind_resp(sequence_number=sequence_number)
        elif smpp_command == SmppCommand.SUBMIT_SM_RESP:
            # the body of this only has `message_id` which is a C-Octet String of variable length upto 65 octets.
            # This field contains the SMSC message_id of the submitted message.
            # It may be used at a later stage to query the status of a message, cancel
            # or replace the message.
            pass
        elif smpp_command == SmppCommand.DELIVER_SM:
            # HEADER::
            # command_length, int, 4octet
            # command_id, int, 4octet. `deliver_sm`
            # command_status, int, 4octet. Unused, Set to NULL.
            # sequence_number, int, 4octet. The associated `deliver_sm_resp` PDU should echo the same sequence_number.

            # BODY::
            # see section 4.6.1 of smpp v3.4 spec
            # we want to handle this pdu, bcoz we are expected to send back deliver_sm_resp
            # the body of this has the following params
            # service_type, C-Octet String, max 6 octets
            # source_addr_ton, Int, 1 octet, can be NULL
            # source_addr_npi, Int, 1 octet, can be NULL
            # source_addr, C-Octet String, max 21 octet, can be NULL
            # dest_addr_ton, Int, 1 octet
            # dest_addr_npi, Int, 1 octet
            # destination_addr,  C-Octet String, max 21 octet
            # esm_class, Int, 1 octet
            # protocol_id, Int, 1 octet
            # priority_flag, Int, 1 octet
            # schedule_delivery_time, C-Octet String, 1 octet, must be set to NULL.
            # validity_period, C-Octet String, 1 octet, must be set to NULL.
            # registered_delivery, Int, 1 octet
            # replace_if_present_flag, Int, 1 octet, must be set to NULL.
            # data_coding, Int, 1 octet
            # sm_default_msg_id, Int, 1 octet, must be set to NULL.
            # sm_length, Int, 1 octet.It is length of short message user data in octets.
            # short_message, C-Octet String, 0-254 octet

            # NB: user's hook has already been called.
            await self.deliver_sm_resp(sequence_number=sequence_number)
        elif smpp_command == SmppCommand.ENQUIRE_LINK:
            # we have to handle this. we have to return enquire_link_resp
            # it has no body
            await self.enquire_link_resp(sequence_number=sequence_number)
        else:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.speficic_handlers",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "command_status": commandStatus.code,
                    "state": commandStatus.description,
                    "error": "the smpp_command:{0} has not been implemented in naz. please create a github issue".format(
                        smpp_command
                    ),
                },
            )

        # call user's hook for responses
        try:
            await self.hook.response(
                smpp_command=smpp_command,
                log_id=log_id,
                hook_metadata=hook_metadata,
                smsc_response=commandStatus,
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.speficic_handlers",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "response hook error",
                    "error": str(e),
                },
            )

    async def unbind(self) -> None:
        """
        send an UNBIND pdu to SMSC.
        """
        smpp_command = SmppCommand.UNBIND
        log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.unbind",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )
        # body
        body = b""

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = 0x00000000  # not used for `unbind`
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.unbind",
                    "stage": "end",
                    "error": str(e),
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
        if sequence_number > self.max_sequence_number:
            # prevent third party sequence_generators from ruining our party
            raise ValueError(
                "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                    sequence_number, self.max_sequence_number
                )
            )

        try:
            await self.correlation_handler.put(
                sequence_number=sequence_number, log_id=log_id, hook_metadata=""
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.unbind",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "correlater put error",
                    "error": str(e),
                },
            )

        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)
        full_pdu = header + body
        # dont queue unbind in SimpleOutboundQueue since we dont want it to be behind 10k msgs etc
        await self.send_data(smpp_command=smpp_command, msg=full_pdu, log_id=log_id)
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.unbind",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

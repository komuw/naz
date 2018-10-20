import struct
import asyncio
import logging
import collections

from . import hooks
from . import nazcodec
from . import sequence
from . import throttle
from . import ratelimiter


# todo:
# 1. add configurable retries
# 2. metrics, what is happening
# 3. run end-to-end integration tests in ci.


class Client:
    """
    """

    def __init__(
        self,
        async_loop,
        smsc_host,
        smsc_port,
        system_id,
        password,
        outboundqueue,
        system_type="",
        addr_ton=0,
        addr_npi=0,
        address_range="",
        encoding="gsm0338",
        interface_version=34,
        service_type="CMT",  # section 5.2.11
        source_addr_ton=0x00000001,  # section 5.2.5
        source_addr_npi=0x00000001,
        dest_addr_ton=0x00000001,
        dest_addr_npi=0x00000001,
        # xxxxxx00 store-and-forward
        # xx0010xx Short Message contains ESME Delivery Acknowledgement
        # 00xxxxxx No specific features selected
        esm_class=0b00001000,  # section 5.2.12
        protocol_id=0x00000000,
        priority_flag=0x00000000,
        schedule_delivery_time="",
        validity_period="",
        # xxxxxx01 SMSC Delivery Receipt requested where final delivery outcome is delivery success or failure
        # xxxx01xx SME Delivery Acknowledgement requested
        # xxx0xxxx No Intermediate notification requested
        # all other values reserved
        registered_delivery=0b00000101,  # see section 5.2.17
        replace_if_present_flag=0x00000000,
        sm_default_msg_id=0x00000000,
        enquire_link_interval=90,
        loglevel="DEBUG",
        log_metadata=None,
        codec_class=None,
        codec_errors_level="strict",
        rateLimiter=None,
        hook=None,
        sequence_generator=None,
        throttle_handler=None,
    ):
        """
        todo: add docs
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
        self.log_metadata.update({"smsc_host": self.smsc_host, "system_id": system_id})

        self.codec_errors_level = codec_errors_level
        self.codec_class = codec_class
        if not self.codec_class:
            self.codec_class = nazcodec.NazCodec(errors=self.codec_errors_level)

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
            "bind_transceiver": 0x00000009,
            "bind_transceiver_resp": 0x80000009,
            "unbind": 0x00000006,
            "unbind_resp": 0x80000006,
            "submit_sm": 0x00000004,
            "submit_sm_resp": 0x80000004,
            "deliver_sm": 0x00000005,
            "deliver_sm_resp": 0x80000005,
            "enquire_link": 0x00000015,
            "enquire_link_resp": 0x80000015,
            "generic_nack": 0x80000000,
        }

        # see section 5.1.3 of smpp ver 3.4 spec document
        CommandStatus = collections.namedtuple("CommandStatus", "code description")
        self.command_statuses = {
            "ESME_ROK": CommandStatus(0x00000000, "Success"),
            "ESME_RINVMSGLEN": CommandStatus(0x00000001, "Message Length is invalid"),
            "ESME_RINVCMDLEN": CommandStatus(0x00000002, "Command Length is invalid"),
            "ESME_RINVCMDID": CommandStatus(0x00000003, "Invalid Command ID"),
            "ESME_RINVBNDSTS": CommandStatus(0x00000004, "Incorrect BIND Status for given command"),
            "ESME_RALYBND": CommandStatus(0x00000005, "ESME Already in Bound State"),
            "ESME_RINVPRTFLG": CommandStatus(0x00000006, "Invalid Priority Flag"),
            "ESME_RINVREGDLVFLG": CommandStatus(0x00000007, "Invalid Registered Delivery Flag"),
            "ESME_RSYSERR": CommandStatus(0x00000008, "System Error"),
            "Reserved": CommandStatus(0x00000009, "Reserved"),
            "ESME_RINVSRCADR": CommandStatus(0x0000000A, "Invalid Source Address"),
            "ESME_RINVDSTADR": CommandStatus(0x0000000B, "Invalid Dest Addr"),
            "ESME_RINVMSGID": CommandStatus(0x0000000C, "Message ID is invalid"),
            "ESME_RBINDFAIL": CommandStatus(0x0000000D, "Bind Failed"),
            "ESME_RINVPASWD": CommandStatus(0x0000000E, "Invalid Password"),
            "ESME_RINVSYSID": CommandStatus(0x0000000F, "Invalid System ID"),
            "REserved": CommandStatus(
                0x00000010, "Reserved"
            ),  # key has different capitalization to avoid clash
            "ESME_RCANCELFAIL": CommandStatus(0x00000011, "Cancel SM Failed"),
            "ReServed": CommandStatus(0x00000012, "Reserved"),
            "ESME_RREPLACEFAIL": CommandStatus(0x00000013, "Replace SM Failed"),
            "ESME_RMSGQFUL": CommandStatus(0x00000014, "Message Queue Full"),
            "ESME_RINVSERTYP": CommandStatus(0x00000015, "Invalid Service Type"),
            # Reserved 0x00000016 - 0x00000032 Reserved
            "ESME_RINVNUMDESTS": CommandStatus(0x00000033, "Invalid number of destinations"),
            "ESME_RINVDLNAME": CommandStatus(0x00000034, "Invalid Distribution List name"),
            # Reserved 0x00000035 - 0x0000003F Reserved
            "ESME_RINVDESTFLAG": CommandStatus(
                0x00000040, "Destination flag is invalid (submit_multi)"
            ),
            "ResErved": CommandStatus(0x00000041, "Reserved"),
            "ESME_RINVSUBREP": CommandStatus(
                0x00000042,
                "Invalid (submit with replace) request(i.e. submit_sm with replace_if_present_flag set)",
            ),
            "ESME_RINVESMCLASS": CommandStatus(0x00000043, "Invalid esm_class field data"),
            "ESME_RCNTSUBDL": CommandStatus(0x00000044, "Cannot Submit to Distribution List"),
            "ESME_RSUBMITFAIL": CommandStatus(0x00000045, "Submit_sm or submit_multi failed"),
            # Reserved 0x00000046 - 0x00000047 Reserved
            "ESME_RINVSRCTON": CommandStatus(0x00000048, "Invalid Source address TON"),
            "ESME_RINVSRCNPI": CommandStatus(0x00000049, "Invalid Source address NPI"),
            "ESME_RINVDSTTON": CommandStatus(0x00000050, "Invalid Destination address TON"),
            "ESME_RINVDSTNPI": CommandStatus(0x00000051, "Invalid Destination address NPI"),
            "ReseRved": CommandStatus(0x00000052, "Reserved"),
            "ESME_RINVSYSTYP": CommandStatus(0x00000053, "Invalid system_type field"),
            "ESME_RINVREPFLAG": CommandStatus(0x00000054, "Invalid replace_if_present flag"),
            "ESME_RINVNUMMSGS": CommandStatus(0x00000055, "Invalid number of messages"),
            # Reserved 0x00000056 - 0x00000057 Reserved
            "ESME_RTHROTTLED": CommandStatus(
                0x00000058, "Throttling error (ESME has exceeded allowed message limits)"
            ),
            # Reserved 0x00000059 - 0x00000060 Reserved
            "ESME_RINVSCHED": CommandStatus(0x00000061, "Invalid Scheduled Delivery Time"),
            "ESME_RINVEXPIRY": CommandStatus(
                0x00000062, "Invalid message validity period (Expiry time)"
            ),
            "ESME_RINVDFTMSGID": CommandStatus(
                0x00000063, "Predefined Message Invalid or Not Found"
            ),
            "ESME_RX_T_APPN": CommandStatus(0x00000064, "ESME Receiver Temporary App Error Code"),
            "ESME_RX_P_APPN": CommandStatus(0x00000065, "ESME Receiver Permanent App Error Code"),
            "ESME_RX_R_APPN": CommandStatus(0x00000066, "ESME Receiver Reject Message Error Code"),
            "ESME_RQUERYFAIL": CommandStatus(0x00000067, "query_sm request failed"),
            # Reserved 0x00000068 - 0x000000BF Reserved
            "ESME_RINVOPTPARSTREAM": CommandStatus(
                0x000000C0, "Error in the optional part of the PDU Body."
            ),
            "ESME_ROPTPARNOTALLWD": CommandStatus(0x000000C1, "Optional Parameter not allowed"),
            "ESME_RINVPARLEN": CommandStatus(0x000000C2, "Invalid Parameter Length."),
            "ESME_RMISSINGOPTPARAM": CommandStatus(
                0x000000C3, "Expected Optional Parameter missing"
            ),
            "ESME_RINVOPTPARAMVAL": CommandStatus(0x000000C4, "Invalid Optional Parameter Value"),
            # Reserved 0x000000C5 - 0x000000FD Reserved
            "ESME_RDELIVERYFAILURE": CommandStatus(
                0x000000FE, "Delivery Failure (used for data_sm_resp)"
            ),
            "ESME_RUNKNOWNERR": CommandStatus(0x000000FF, "Unknown Error"),
            # Reserved for SMPP extension 0x00000100 - 0x000003FF Reserved for SMPP extension
            # Reserved for SMSC vendor specific errors 0x00000400 - 0x000004FF Reserved for SMSC vendor specific errors
            # Reserved 0x00000500 - 0xFFFFFFFF Reserved
        }

        # see section 5.2.19
        DataCoding = collections.namedtuple("DataCoding", "code description")
        # the keys to the `data_codings` dict are the names of the codecs as defined in https://docs.python.org/3.6/library/codecs.html
        # that is if they exist in that document.
        self.data_codings = {
            "gsm0338": DataCoding(0b00000000, "SMSC Default Alphabet"),
            "ascii": DataCoding(0b00000001, "IA5(CCITT T.50) / ASCII(ANSI X3.4)"),
            "octet_unspecified_I": DataCoding(0b00000010, "Octet unspecified(8 - bit binary)"),
            "latin_1": DataCoding(0b00000011, "Latin 1 (ISO - 8859 - 1)"),
            "octet_unspecified_II": DataCoding(0b00000100, "Octet unspecified(8 - bit binary)"),
            # iso2022_jp, iso2022jp and iso-2022-jp are aliases
            # see: https://stackoverflow.com/a/43240579/2768067
            "iso2022_jp": DataCoding(0b00000101, "JIS(X 0208 - 1990)"),
            "iso8859_5": DataCoding(0b00000110, "Cyrllic(ISO - 8859 - 5)"),
            "iso8859_8": DataCoding(0b00000111, "Latin / Hebrew(ISO - 8859 - 8)"),
            # see: https://stackoverflow.com/a/14488478/2768067
            "utf_16_be": DataCoding(0b00001000, "UCS2(ISO / IEC - 10646)"),
            "ucs2": DataCoding(0b00001000, "UCS2(ISO / IEC - 10646)"),
            "shift_jis": DataCoding(0b00001001, "Pictogram Encoding"),
            "iso2022jp": DataCoding(0b00001010, "ISO - 2022 - JP(Music Codes)"),
            "reservedI": DataCoding(0b00001011, "reserved"),
            "reservedII": DataCoding(0b00001100, "reserved"),
            # not the same as iso2022_jp but ...
            "iso-2022-jp": DataCoding(0b00001101, "Extended Kanji JIS(X 0212 - 1990)"),
            "euc_kr": DataCoding(0b00001110, "KS C 5601"),
            # 00001111 - 10111111 reserved
            # 0b1100xxxx GSM MWI control - see [GSM 03.38]
            # 0b1101xxxx GSM MWI control - see [GSM 03.38]
            # 0b1110xxxx reserved
            # 0b1111xxxx GSM message class control - see [GSM 03.38]
        }
        # also see:
        # https://github.com/praekelt/vumi/blob/767eac623c81cc4b2e6ea9fbd6a3645f121ef0aa/vumi/transports/smpp/processors/default.py#L260

        self.data_coding = self.data_codings[self.encoding].code

        self.reader = None
        self.writer = None

        # NB: currently, naz only uses to log levels; INFO and EXCEPTION
        extra_log_data = {"log_metadata": self.log_metadata}
        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(self.loglevel)
        self.logger = NazLoggingAdapter(self.logger, extra_log_data)

        self.rateLimiter = rateLimiter
        if not self.rateLimiter:
            self.rateLimiter = ratelimiter.SimpleRateLimiter(logger=self.logger)

        self.hook = hook
        if not self.hook:
            self.hook = hooks.SimpleHook(logger=self.logger)

        self.throttle_handler = throttle_handler
        if not self.throttle_handler:
            self.throttle_handler = throttle.SimpleThrottleHandler(logger=self.logger)

        # dictionary of sequence_number and their corresponding correlation_id
        # this will be used to track different pdu's and user generated correlation_id
        self.seq_correl = {}

    def search_by_command_id_code(self, command_id_code):
        for key, val in self.command_ids.items():
            if val == command_id_code:
                return key
        return None

    def search_by_command_status_code(self, command_status_code):
        for key, val in self.command_statuses.items():
            if val.code == command_status_code:
                return key, val
        return None, None

    async def connect(self):
        self.logger.info("{}".format({"event": "connect", "stage": "start"}))
        reader, writer = await asyncio.open_connection(
            self.smsc_host, self.smsc_port, loop=self.async_loop
        )
        self.reader = reader
        self.writer = writer
        self.logger.info("{}".format({"event": "connect", "stage": "end"}))
        return reader, writer

    async def tranceiver_bind(self):
        self.logger.info("{}".format({"event": "tranceiver_bind", "stage": "start"}))
        # body
        body = b""
        body = (
            body
            + self.codec_class.encode(self.system_id, self.encoding)
            + chr(0).encode("latin-1")
            + self.codec_class.encode(self.password, self.encoding)
            + chr(0).encode("latin-1")
            + self.codec_class.encode(self.system_type, self.encoding)
            + chr(0).encode("latin-1")
            + struct.pack(">I", self.interface_version)
            + struct.pack(">I", self.addr_ton)
            + struct.pack(">I", self.addr_npi)
            + self.codec_class.encode(self.address_range, self.encoding)
            + chr(0).encode("latin-1")
        )

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids["bind_transceiver"]
        # the status for success see section 5.1.3
        command_status = self.command_statuses["ESME_ROK"].code
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self.logger.exception(
                "{}".format({"event": "tranceiver_bind", "stage": "end", "error": str(e)})
            )

        if sequence_number > self.max_sequence_number:
            # prevent third party sequence_generators from ruining our party
            raise ValueError(
                "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                    sequence_number, self.max_sequence_number
                )
            )
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        await self.send_data(smpp_event="bind_transceiver", msg=full_pdu)
        self.logger.info("{}".format({"event": "tranceiver_bind", "stage": "end"}))
        return full_pdu

    async def enquire_link(self, correlation_id=None, TESTING=False):
        """
        HEADER::
        # enquire_link has the following pdu header:
        command_length, int, 4octet
        command_id, int, 4octet. `enquire_link`
        command_status, int, 4octet. Not used. Set to NULL
        sequence_number, int, 4octet.

        `enquire_link` has no body.
        """
        while True:
            self.logger.info(
                "{}".format(
                    {"event": "enquire_link", "stage": "start", "correlation_id": correlation_id}
                )
            )
            # body
            body = b""

            # header
            command_length = 16 + len(body)  # 16 is for headers
            command_id = self.command_ids["enquire_link"]
            command_status = 0x00000000  # not used for `enquire_link`
            try:
                sequence_number = self.sequence_generator.next_sequence()
            except Exception as e:
                self.logger.exception(
                    "{}".format(
                        {
                            "event": "enquire_link",
                            "stage": "end",
                            "error": str(e),
                            "correlation_id": correlation_id,
                        }
                    )
                )
            if sequence_number > self.max_sequence_number:
                # prevent third party sequence_generators from ruining our party
                raise ValueError(
                    "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                        sequence_number, self.max_sequence_number
                    )
                )
            header = struct.pack(
                ">IIII", command_length, command_id, command_status, sequence_number
            )

            full_pdu = header + body
            # dont queue enquire_link in SimpleOutboundQueue since we dont want it to be behind 10k msgs etc
            await self.send_data(smpp_event="enquire_link", msg=full_pdu)
            self.logger.info(
                "{}".format(
                    {"event": "enquire_link", "stage": "end", "correlation_id": correlation_id}
                )
            )
            if TESTING:
                return full_pdu
            await asyncio.sleep(self.enquire_link_interval)

    async def enquire_link_resp(self, sequence_number, correlation_id=None):
        """
        HEADER::
        # enquire_link_resp has the following pdu header:
        command_length, int, 4octet
        command_id, int, 4octet. `enquire_link_resp`
        command_status, int, 4octet. ESME_ROK (Success)
        sequence_number, int, 4octet. Set to the same sequence number of original `enquire_link` PDU

        `enquire_link_resp` has no body.
        """
        # body
        self.logger.info(
            "{}".format(
                {"event": "enquire_link_resp", "stage": "start", "correlation_id": correlation_id}
            )
        )
        body = b""

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids["enquire_link_resp"]
        command_status = self.command_statuses["ESME_ROK"].code
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        item_to_enqueue = {
            "correlation_id": correlation_id,
            "pdu": full_pdu,
            "smpp_event": "enquire_link_resp",
        }
        try:
            await self.outboundqueue.enqueue(item_to_enqueue)
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "enquire_link_resp",
                        "stage": "end",
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                )
            )
        self.logger.info(
            "{}".format(
                {"event": "enquire_link_resp", "stage": "end", "correlation_id": correlation_id}
            )
        )

    async def unbind_resp(self, sequence_number, correlation_id=None):
        """
        HEADER::
        # unbind_resp has the following pdu header:
        command_length, int, 4octet
        command_id, int, 4octet. `unbind_resp`
        command_status, int, 4octet. Indicates outcome of original unbind request, eg ESME_ROK (Success)
        sequence_number, int, 4octet. Set to the same sequence number of original `unbind` PDU

        `unbind_resp` has no body.
        """
        self.logger.info(
            "{}".format(
                {"event": "unbind_resp", "stage": "start", "correlation_id": correlation_id}
            )
        )

        # body
        body = b""

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids["unbind_resp"]
        command_status = self.command_statuses["ESME_ROK"].code
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        # dont queue unbind_resp in SimpleOutboundQueue since we dont want it to be behind 10k msgs etc
        await self.send_data(smpp_event="unbind_resp", msg=full_pdu)
        self.logger.info(
            "{}".format({"event": "unbind_resp", "stage": "end", "correlation_id": correlation_id})
        )

    async def deliver_sm_resp(self, sequence_number, correlation_id=None):
        """
        HEADER::
        # deliver_sm_resp has the following pdu header:
        command_length, int, 4octet
        command_id, int, 4octet. `deliver_sm_resp`
        command_status, int, 4octet. Indicates outcome of deliver_sm request, eg. ESME_ROK (Success)
        sequence_number, int, 4octet.  Set to the same sequence_number of `deliver_sm` PDU.

        BODY::
        message_id, c-octet String, 1octet. This field is unused and is set to NULL.
        """
        self.logger.info(
            "{}".format(
                {"event": "deliver_sm_resp", "stage": "start", "correlation_id": correlation_id}
            )
        )
        # body
        body = b""
        message_id = ""
        body = body + self.codec_class.encode(message_id, self.encoding) + chr(0).encode("latin-1")

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids["deliver_sm_resp"]
        command_status = self.command_statuses["ESME_ROK"].code
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        item_to_enqueue = {
            "correlation_id": correlation_id,
            "pdu": full_pdu,
            "smpp_event": "deliver_sm_resp",
        }
        try:
            await self.outboundqueue.enqueue(item_to_enqueue)
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "deliver_sm_resp",
                        "stage": "end",
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                )
            )
        self.logger.info(
            "{}".format(
                {"event": "deliver_sm_resp", "stage": "end", "correlation_id": correlation_id}
            )
        )

    # this method just enqueues a submit_sm msg to queue
    async def submit_sm(self, short_message, correlation_id, source_addr, destination_addr):
        """
        HEADER::
        # submit_sm has the following pdu header:
        command_length, int, 4octet
        command_id, int, 4octet. `submit_sm`
        command_status, int, 4octet. Not used. Set to NULL
        sequence_number, int, 4octet.  The associated submit_sm_resp PDU will echo this sequence number.

        BODY::
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
        NB: 1. Applications which need to send messages longer than 254 octets should use the `message_payload` optional parameter.
               In this case the `sm_length` field should be set to zero
               u cant use both `short_message` and `message_payload`
            2. Octet String - A series of octets, not necessarily NULL terminated.
        """
        self.logger.info(
            "{}".format(
                {
                    "event": "submit_sm",
                    "stage": "start",
                    "correlation_id": correlation_id,
                    "short_message": short_message,
                    "source_addr": source_addr,
                    "destination_addr": destination_addr,
                }
            )
        )
        item_to_enqueue = {
            "smpp_event": "submit_sm",
            "short_message": short_message,
            "correlation_id": correlation_id,
            "source_addr": source_addr,
            "destination_addr": destination_addr,
        }
        try:
            await self.outboundqueue.enqueue(item_to_enqueue)
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "submit_sm",
                        "stage": "end",
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                )
            )
        self.logger.info(
            "{}".format(
                {
                    "event": "submit_sm",
                    "stage": "end",
                    "correlation_id": correlation_id,
                    "short_message": short_message,
                    "source_addr": source_addr,
                    "destination_addr": destination_addr,
                }
            )
        )

    async def build_submit_sm_pdu(
        self, short_message, correlation_id, source_addr, destination_addr
    ):
        self.logger.info(
            "{}".format(
                {
                    "event": "build_submit_sm_pdu",
                    "stage": "start",
                    "correlation_id": correlation_id,
                    "short_message": short_message,
                    "source_addr": source_addr,
                    "destination_addr": destination_addr,
                }
            )
        )
        encoded_short_message = self.codec_class.encode(short_message, self.encoding)
        sm_length = len(encoded_short_message)

        # body
        body = b""
        body = (
            body
            + self.codec_class.encode(self.service_type, self.encoding)
            + chr(0).encode("latin-1")
            + struct.pack(">B", self.source_addr_ton)
            + struct.pack(">B", self.source_addr_npi)
            + self.codec_class.encode(source_addr, self.encoding)
            + chr(0).encode("latin-1")
            + struct.pack(">B", self.dest_addr_ton)
            + struct.pack(">B", self.dest_addr_npi)
            + self.codec_class.encode(destination_addr, self.encoding)
            + chr(0).encode("latin-1")
            + struct.pack(">B", self.esm_class)
            + struct.pack(">B", self.protocol_id)
            + struct.pack(">B", self.priority_flag)
            + self.codec_class.encode(self.schedule_delivery_time, self.encoding)
            + chr(0).encode("latin-1")
            + self.codec_class.encode(self.validity_period, self.encoding)
            + chr(0).encode("latin-1")
            + struct.pack(">B", self.registered_delivery)
            + struct.pack(">B", self.replace_if_present_flag)
            + struct.pack(">B", self.data_coding)
            + struct.pack(">B", self.sm_default_msg_id)
            + struct.pack(">B", sm_length)
            + self.codec_class.encode(short_message, self.encoding)
        )

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids["submit_sm"]
        # the status for success see section 5.1.3
        command_status = 0x00000000  # not used for `submit_sm`
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "build_submit_sm_pdu",
                        "stage": "end",
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                )
            )
        if sequence_number > self.max_sequence_number:
            # prevent third party sequence_generators from ruining our party
            raise ValueError(
                "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                    sequence_number, self.max_sequence_number
                )
            )
        # associate sequence_number and user supplied correlation_id
        self.seq_correl[sequence_number] = correlation_id
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)
        full_pdu = header + body

        self.logger.info(
            "{}".format(
                {
                    "event": "build_submit_sm_pdu",
                    "stage": "end",
                    "correlation_id": correlation_id,
                    "short_message": short_message,
                    "source_addr": source_addr,
                    "destination_addr": destination_addr,
                }
            )
        )
        return full_pdu

    async def send_data(self, smpp_event, msg, correlation_id=None):
        """
        This method does not block; it buffers the data and arranges for it to be sent out asynchronously.
        see: https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.write
        """
        # todo: look at `set_write_buffer_limits` and `get_write_buffer_limits` methods
        # print("get_write_buffer_limits:", writer.transport.get_write_buffer_limits())
        log_msg = ""
        try:
            log_msg = self.codec_class.decode(msg, self.encoding)
        except Exception:
            pass
        self.logger.info(
            "{}".format(
                {
                    "event": "send_data",
                    "stage": "start",
                    "smpp_event": smpp_event,
                    "correlation_id": correlation_id,
                    "msg": log_msg,
                }
            )
        )

        if isinstance(msg, str):
            msg = self.codec_class.encode(msg, self.encoding)

        # call user's hook for requests
        try:
            await self.hook.request(smpp_event=smpp_event, correlation_id=correlation_id)
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "send_data",
                        "stage": "end",
                        "smpp_event": smpp_event,
                        "correlation_id": correlation_id,
                        "state": "request hook error",
                        "error": str(e),
                    }
                )
            )

        self.writer.write(msg)
        await self.writer.drain()
        self.logger.info(
            "{}".format(
                {
                    "event": "send_data",
                    "stage": "end",
                    "smpp_event": smpp_event,
                    "correlation_id": correlation_id,
                    "msg": log_msg,
                }
            )
        )

    async def send_forever(self, TESTING=False):
        while True:
            self.logger.info("{}".format({"event": "send_forever", "stage": "start"}))

            # TODO: there are so many try-except classes in this func.
            # do something about that.
            try:
                # check with throttle handler
                send_request = await self.throttle_handler.allow_request()
            except Exception as e:
                self.logger.exception(
                    "{}".format(
                        {
                            "event": "send_forever",
                            "stage": "end",
                            "state": "send_forever error",
                            "error": str(e),
                        }
                    )
                )
                continue
            if send_request:
                try:
                    # rate limit ourselves
                    await self.rateLimiter.limit()
                except Exception as e:
                    self.logger.exception(
                        "{}".format(
                            {
                                "event": "send_forever",
                                "stage": "end",
                                "state": "send_forever error",
                                "error": str(e),
                            }
                        )
                    )
                    continue

                try:
                    item_to_dequeue = await self.outboundqueue.dequeue()
                except Exception as e:
                    self.logger.exception(
                        "{}".format(
                            {
                                "event": "send_forever",
                                "stage": "end",
                                "state": "send_forever error",
                                "error": str(e),
                            }
                        )
                    )
                    continue
                try:
                    correlation_id = item_to_dequeue["correlation_id"]
                    smpp_event = item_to_dequeue["smpp_event"]
                    if smpp_event == "submit_sm":
                        short_message = item_to_dequeue["short_message"]
                        correlation_id = item_to_dequeue["correlation_id"]
                        source_addr = item_to_dequeue["source_addr"]
                        destination_addr = item_to_dequeue["destination_addr"]
                        full_pdu = await self.build_submit_sm_pdu(
                            short_message, correlation_id, source_addr, destination_addr
                        )
                    else:
                        full_pdu = item_to_dequeue["pdu"]
                except KeyError as e:
                    self.logger.exception(
                        "{}".format(
                            {
                                "event": "send_forever",
                                "stage": "end",
                                "state": "send_forever error",
                                "error": str(e),
                            }
                        )
                    )
                    continue

                await self.send_data(
                    smpp_event=smpp_event, msg=full_pdu, correlation_id=correlation_id
                )
                self.logger.info(
                    "{}".format(
                        {
                            "event": "send_forever",
                            "stage": "end",
                            "correlation_id": correlation_id,
                            "smpp_event": smpp_event,
                            "send_request": send_request,
                        }
                    )
                )
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return item_to_dequeue
            else:
                # throttle_handler didn't allow us to send request.
                self.logger.info(
                    "{}".format(
                        {"event": "send_forever", "stage": "end", "send_request": send_request}
                    )
                )
                try:
                    await asyncio.sleep(await self.throttle_handler.throttle_delay())
                except Exception as e:
                    self.logger.exception(
                        "{}".format(
                            {
                                "event": "send_forever",
                                "stage": "end",
                                "state": "send_forever error",
                                "error": str(e),
                            }
                        )
                    )
                    continue
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return "throttle_handler_denied_request"
                continue

    async def receive_data(self):
        """
        """
        while True:
            self.logger.info("{}".format({"event": "receive_data", "stage": "start"}))
            # todo: look at `pause_reading` and `resume_reading` methods
            command_length_header_data = await self.reader.read(4)
            if command_length_header_data == b"":
                self.logger.info(
                    "{}".format(
                        {"event": "receive_data", "stage": "start", "state": "no data received"}
                    )
                )
                # todo: sleep in an exponetial manner upto a maximum then wrap around.
                await asyncio.sleep(8)
                continue

            total_pdu_length = struct.unpack(">I", command_length_header_data)[0]

            MSGLEN = total_pdu_length - 4
            chunks = []
            bytes_recd = 0
            while bytes_recd < MSGLEN:
                chunk = await self.reader.read(min(MSGLEN - bytes_recd, 2048))
                if chunk == b"":
                    self.logger.exception(
                        "{}".format(
                            {
                                "event": "receive_data",
                                "stage": "end",
                                "state": "socket connection broken",
                            }
                        )
                    )
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            full_pdu_data = command_length_header_data + b"".join(chunks)
            await self.parse_response_pdu(full_pdu_data)
            self.logger.info("{}".format({"event": "receive_data", "stage": "end"}))

    async def parse_response_pdu(self, pdu):
        """
        """
        self.logger.info("{}".format({"event": "parse_response_pdu", "stage": "start"}))

        header_data = pdu[:16]
        command_length_header_data = header_data[:4]
        total_pdu_length = struct.unpack(">I", command_length_header_data)[0]

        command_id_header_data = header_data[4:8]
        command_status_header_data = header_data[8:12]
        sequence_number_header_data = header_data[12:16]

        command_id = struct.unpack(">I", command_id_header_data)[0]
        command_status = struct.unpack(">I", command_status_header_data)[0]
        sequence_number = struct.unpack(">I", sequence_number_header_data)[0]
        # get associated user supplied correlation_id if any, free mem while at it.
        correlation_id = self.seq_correl.pop(sequence_number, None)

        smpp_event = self.search_by_command_id_code(command_id)
        if not smpp_event:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "parse_response_pdu",
                        "stage": "end",
                        "correlation_id": correlation_id,
                        "state": "command_id:{0} is unknown.".format(command_id),
                    }
                )
            )
            raise ValueError("command_id:{0} is unknown.".format(command_id))

        # call user's hook for responses
        try:
            # todo: send correlation_id to response hook, when we are eventually able to relate
            # everything to a correlation_id
            await self.hook.response(smpp_event=smpp_event, correlation_id=correlation_id)
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "parse_response_pdu",
                        "stage": "end",
                        "smpp_event": smpp_event,
                        "correlation_id": correlation_id,
                        "state": "response hook error",
                        "error": str(e),
                    }
                )
            )

        pdu_body = b""
        if total_pdu_length > 16:
            pdu_body = pdu[16:]
        await self.speficic_handlers(
            smpp_event=smpp_event,
            command_status=command_status,
            sequence_number=sequence_number,
            correlation_id=correlation_id,
            unparsed_pdu_body=pdu_body,
            total_pdu_length=total_pdu_length,
        )
        self.logger.info(
            "{}".format(
                {
                    "event": "parse_response_pdu",
                    "stage": "end",
                    "smpp_event": smpp_event,
                    "correlation_id": correlation_id,
                    "command_status": command_status,
                }
            )
        )

    async def speficic_handlers(
        self,
        smpp_event,
        command_status,
        sequence_number,
        correlation_id,
        unparsed_pdu_body,
        total_pdu_length,
    ):
        """
        this handles parsing speficic
        """
        # todo: pliz find a better way of doing this.
        # this will cause global warming with useless computation
        command_status_name, command_status_value = self.search_by_command_status_code(
            command_status
        )

        if command_status != self.command_statuses["ESME_ROK"].code:
            # we got an error from SMSC
            self.logger.exception(
                "{}".format(
                    {
                        "event": "speficic_handlers",
                        "stage": "start",
                        "smpp_event": smpp_event,
                        "correlation_id": correlation_id,
                        "command_status": command_status_value.code,
                        "state": command_status_value.description,
                    }
                )
            )
        else:
            self.logger.info(
                "{}".format(
                    {
                        "event": "speficic_handlers",
                        "stage": "start",
                        "smpp_event": smpp_event,
                        "correlation_id": correlation_id,
                        "command_status": command_status_value.code,
                        "state": command_status_value.description,
                    }
                )
            )

        try:
            # call throttling handler
            if command_status == self.command_statuses["ESME_ROK"].code:
                await self.throttle_handler.not_throttled()
            elif command_status == self.command_statuses["ESME_RTHROTTLED"].code:
                await self.throttle_handler.throttled()
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "speficic_handlers",
                        "stage": "end",
                        "error": str(e),
                        "smpp_event": smpp_event,
                        "correlation_id": correlation_id,
                        "state": command_status_value.description,
                    }
                )
            )

        if smpp_event in [
            "bind_transceiver",
            "bind_transceiver_resp",
            # the body of `bind_transceiver_resp` only has `system_id` which is a
            # C-Octet String of variable length upto 16 octets
            "unbind_resp",
            "submit_sm",  # We dont expect SMSC to send `submit_sm` to us.
            "deliver_sm_resp",
            # we will never send a deliver_sm request to SMSC, which means we never
            # have to handle deliver_sm_resp
            "enquire_link_resp",
            "generic_nack",  # we can ignore this
        ]:
            # we never have to handle this
            pass
        elif smpp_event == "unbind":
            # we need to handle this since we need to send unbind_resp
            # it has no body
            await self.unbind_resp(sequence_number=sequence_number, correlation_id=correlation_id)
        elif smpp_event == "submit_sm_resp":
            # the body of this only has `message_id` which is a C-Octet String of variable length upto 65 octets.
            # This field contains the SMSC message_id of the submitted message.
            # It may be used at a later stage to query the status of a message, cancel
            # or replace the message.
            # todo: call user's hook in here. we should correlate user's supplied correlation_id and sequence_number
            pass
        elif smpp_event == "deliver_sm":
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
            await self.deliver_sm_resp(
                sequence_number=sequence_number, correlation_id=correlation_id
            )
        elif smpp_event == "enquire_link":
            # we have to handle this. we have to return enquire_link_resp
            # it has no body
            await self.enquire_link_resp(
                sequence_number=sequence_number, correlation_id=correlation_id
            )
        else:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "speficic_handlers",
                        "stage": "end",
                        "smpp_event": smpp_event,
                        "correlation_id": correlation_id,
                        "command_status": command_status_value.code,
                        "state": command_status_value.description,
                        "error": "unknown command",
                    }
                )
            )

    async def unbind(self, correlation_id=None):
        """
        HEADER::
        # unbind has the following pdu header:
        command_length, int, 4octet
        command_id, int, 4octet. `unbind`
        command_status, int, 4octet. Not used. Set to NULL
        sequence_number, int, 4octet.

        `unbind` has no body.

        clients/users should call this method when winding down.
        """
        self.logger.info(
            "{}".format({"event": "unbind", "stage": "start", "correlation_id": correlation_id})
        )
        # body
        body = b""

        # header
        command_length = 16 + len(body)  # 16 is for headers
        command_id = self.command_ids["unbind"]
        command_status = 0x00000000  # not used for `unbind`
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self.logger.exception(
                "{}".format(
                    {
                        "event": "unbind",
                        "stage": "end",
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                )
            )
        if sequence_number > self.max_sequence_number:
            # prevent third party sequence_generators from ruining our party
            raise ValueError(
                "the sequence_number: {0} is greater than the max: {1} allowed by SMPP spec.".format(
                    sequence_number, self.max_sequence_number
                )
            )
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        # dont queue unbind in SimpleOutboundQueue since we dont want it to be behind 10k msgs etc
        await self.send_data(smpp_event="unbind", msg=full_pdu)
        self.logger.info(
            "{}".format({"event": "unbind", "stage": "end", "correlation_id": correlation_id})
        )


class NazLoggingAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'log_metadata' key, whose value in brackets is apended to the log message.
    """

    def process(self, msg, kwargs):
        return "{0} {1}".format(msg, self.extra.get("log_metadata")), kwargs

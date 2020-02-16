import os
import struct
import random
import socket
import string
import typing
import asyncio
import logging


# pytype: disable=pyi-error
from . import log
from . import hooks
from . import protocol
from . import sequence
from . import throttle
from . import correlater
from . import ratelimiter
from . import codec as the_codec
from . import broker as the_broker


from .state import (
    SmppCommand,
    CommandStatus,
    SmppDataCoding,
    SmppOptionalTag,
    SmppSessionState,
    SmppCommandStatus,
)

# pytype: disable=pyi-error


class Client:
    """
    The SMPP client that will interact with SMSC/server.

    Example declaration:

    .. highlight:: python
    .. code-block:: python

        import os
        import asyncio
        import naz

        broker = naz.broker.SimpleBroker(maxsize=1000)
        client = naz.Client(
                smsc_host="127.0.0.1",
                smsc_port=2775,
                system_id="smppclient1",
                password=os.getenv("password", "password"),
                broker=broker,
            )

        # 1. connect to the SMSC host
        # 2. bind to the SMSC host
        # 3. send any queued messages to SMSC
        # 4. read any data from SMSC
        # 5. continually check the state of the SMSC
        tasks = asyncio.gather(
            client.connect(),
            client.tranceiver_bind(),
            client.dequeue_messages(),
            client.receive_data(),
            client.enquire_link(),
        )
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tasks)
    """

    def __init__(
        self,
        smsc_host: str,
        smsc_port: int,
        system_id: str,
        password: str,
        broker: the_broker.BaseBroker,
        client_id: typing.Union[None, str] = None,
        # Reference made to NULL settings of Octet-String fields implies that the field
        # consists of a single NULL character, i.e., an octet encoded with value 0x00 (zero).
        # see section 3.1 of v3.4 smpp specification.
        #
        # In Python; "".encode("ascii") + chr(0).encode("ascii") == chr(0).encode("ascii")
        # thus it is okay to use ""(empty string) to represent NULL for c-octet strings
        system_type: str = "",
        addr_ton: int = 0x00,
        addr_npi: int = 0x00,
        address_range: str = "",
        interface_version: int = 0x34,
        enquire_link_interval: float = 55.00,
        logger: typing.Union[None, logging.Logger] = None,
        codec: typing.Union[None, the_codec.BaseCodec] = None,
        rate_limiter: typing.Union[None, ratelimiter.BaseRateLimiter] = None,
        hook: typing.Union[None, hooks.BaseHook] = None,
        sequence_generator: typing.Union[None, sequence.BaseSequenceGenerator] = None,
        throttle_handler: typing.Union[None, throttle.BaseThrottleHandler] = None,
        correlation_handler: typing.Union[None, correlater.BaseCorrelater] = None,
        drain_duration: float = 8.00,
        socket_timeout: float = 30.0,
    ) -> None:
        """
        Parameters:
            smsc_host:	the IP address(or domain name) of the SMSC gateway/server
            smsc_port:	the port at which SMSC is listening on
            system_id:	Identifies the ESME system requesting to bind as a transceiver with the SMSC.
            password:	The password to be used by the SMSC to authenticate the ESME requesting to bind.
            broker:	python class instance implementing some queueing mechanism. \
                messages to be sent to SMSC are queued using the said mechanism before been sent
            client_id:	a unique string identifying a naz client class instance
            system_type:	Identifies the type of ESME system requesting to bind with the SMSC.
            addr_ton:	Type of Number of the ESME address.
            addr_npi:	Numbering Plan Indicator (NPI) for ESME address(es) served via this SMPP transceiver session
            address_range:	A single ESME address or a range of ESME addresses served via this SMPP transceiver session.
            interface_version:	Indicates the version of the SMPP protocol supported by the ESME.
            enquire_link_interval:	time in seconds to wait before sending an enquire_link request to SMSC to check on its status
            logger: python `logger <https://docs.python.org/3/library/logging.html#logging.Logger>`_ instance to be used for logging
            codec: python class instance, that is a child class of `naz.codec.BaseCodec` to be used to encode/decode messages.
            rate_limiter: python class instance implementing rate limitation
            hook: python class instance implemeting functionality/hooks to be called by naz \
                just before sending request to SMSC and just after getting response from SMSC
            sequence_generator:	python class instance used to generate sequence_numbers
            throttle_handler: python class instance implementing functionality of what todo when naz starts getting throttled responses from SMSC
            correlation_handler: A python class instance that naz uses to store relations between \
                SMPP sequence numbers and user applications' log_id's and/or hook_metadata.
            drain_duration: duration in seconds that `naz` will wait for after receiving a termination signal.
            socket_timeout: duration that `naz` will wait, for socket/connection related activities with SMSC, before timing out

        Raises:
            NazClientError: raised if there’s an error instantiating a naz Client.
        """
        self._validate_client_args(
            smsc_host=smsc_host,
            smsc_port=smsc_port,
            system_id=system_id,
            password=password,
            broker=broker,
            client_id=client_id,
            system_type=system_type,
            addr_ton=addr_ton,
            addr_npi=addr_npi,
            address_range=address_range,
            interface_version=interface_version,
            enquire_link_interval=enquire_link_interval,
            logger=logger,
            codec=codec,
            rate_limiter=rate_limiter,
            hook=hook,
            sequence_generator=sequence_generator,
            throttle_handler=throttle_handler,
            correlation_handler=correlation_handler,
            drain_duration=drain_duration,
            socket_timeout=socket_timeout,
        )

        self._PID = os.getpid()
        self.smsc_host = smsc_host
        self.smsc_port = smsc_port
        self.system_id = system_id
        self.password = password
        self.broker = broker

        if client_id is not None:
            self.client_id = client_id
        else:
            self.client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=17))

        self.system_type = system_type
        self.interface_version = interface_version
        self.addr_ton = addr_ton
        self.addr_npi = addr_npi
        self.address_range = address_range

        if sequence_generator is not None:
            self.sequence_generator = sequence_generator
        else:
            self.sequence_generator = sequence.SimpleSequenceGenerator()

        self.max_sequence_number = 0x7FFFFFFF

        if logger is not None:
            self.logger = logger
        else:
            self.logger = log.SimpleLogger(
                "naz.client",
                log_metadata={
                    "smsc_host": self.smsc_host,
                    "system_id": system_id,
                    "client_id": self.client_id,
                    "pid": self._PID,
                },
            )
        self._sanity_check_logger()

        if codec is not None:
            self.codec = codec
        else:
            self.codec = the_codec.SimpleCodec()

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
            # naz currently does not handle the following smpp commands.
            # open a github issue if you use naz and require support of a command in this list
            SmppCommand.BIND_RECEIVER_RESP: 0x80000001,
            SmppCommand.BIND_TRANSMITTER_RESP: 0x80000002,
            SmppCommand.QUERY_SM: 0x00000003,
            SmppCommand.QUERY_SM_RESP: 0x80000003,
            SmppCommand.REPLACE_SM: 0x00000007,
            SmppCommand.REPLACE_SM_RESP: 0x80000007,
            SmppCommand.CANCEL_SM: 0x00000008,
            SmppCommand.CANCEL_SM_RESP: 0x80000008,
            SmppCommand.SUBMIT_MULTI: 0x00000021,
            SmppCommand.SUBMIT_MULTI_RESP: 0x80000021,
            SmppCommand.OUTBIND: 0x0000000B,
            SmppCommand.ALERT_NOTIFICATION: 0x00000102,
            SmppCommand.DATA_SM: 0x00000103,
            SmppCommand.DATA_SM_RESP: 0x80000103,
            SmppCommand.RESERVED_A: 0x0000000A,
            SmppCommand.RESERVED_B: 0x8000000A,
            SmppCommand.RESERVED_C: 0x00000100,
            SmppCommand.RESERVED_D: 0x80000100,
            SmppCommand.RESERVED_E: 0x00000101,
            SmppCommand.RESERVED_F: 0x80000101,
            SmppCommand.RESERVED_G: 0x80000102,
            SmppCommand.RESERVED_LIST_A: [0x0000000C, 0x00000014],
            SmppCommand.RESERVED_LIST_B: [0x8000000B, 0x80000014],
            SmppCommand.RESERVED_LIST_C: [0x00000016, 0x00000020],
            SmppCommand.RESERVED_LIST_D: [0x80000016, 0x80000020],
            SmppCommand.RESERVED_LIST_E: [0x00000022, 0x000000FF],
            SmppCommand.RESERVED_LIST_F: [0x80000022, 0x800000FF],
            SmppCommand.RESERVED_LIST_G: [0x00010300, 0xFFFFFFFF],
            SmppCommand.RESERVED_LIST_H: [0x00010000, 0x000101FF],
            SmppCommand.RESERVED_LIST_I: [0x80010000, 0x800101FF],
            SmppCommand.RESERVED_FOR_SMPP_EXTENSION_A: [0x00000104, 0x0000FFFF],
            SmppCommand.RESERVED_FOR_SMPP_EXTENSION_B: [0x80000104, 0x8000FFFF],
            SmppCommand.RESERVED_FOR_SMSC_VENDOR_A: [0x00010200, 0x000102FF],
            SmppCommand.RESERVED_FOR_SMSC_VENDOR_B: [0x80010200, 0x800102FF],
        }

        self.data_coding = self._find_data_coding(self.codec.encoding)

        self.reader: typing.Union[None, asyncio.streams.StreamReader] = None
        self.writer: typing.Union[None, asyncio.streams.StreamWriter] = None

        if rate_limiter is not None:
            self.rate_limiter = rate_limiter
        else:
            self.rate_limiter = ratelimiter.SimpleRateLimiter(logger=self.logger)

        if hook is not None:
            self.hook = hook
        else:
            self.hook = hooks.SimpleHook(logger=self.logger)

        if throttle_handler is not None:
            self.throttle_handler = throttle_handler
        else:
            self.throttle_handler = throttle.SimpleThrottleHandler(logger=self.logger)

        # class storing SMPP sequence_number and their corresponding log_id and/or hook_metadata
        # this will be used to track different pdu's and user generated log_id
        if correlation_handler is not None:
            self.correlation_handler = correlation_handler
        else:
            self.correlation_handler = correlater.SimpleCorrelater()

        self.naz_message_protocol_version = protocol.NAZ_MESSAGE_PROTOCOL_VERSION

        self.current_session_state = SmppSessionState.CLOSED
        self._header_pdu_length = 16

        self.drain_duration = drain_duration
        self.socket_timeout = socket_timeout
        self.SHOULD_SHUT_DOWN: bool = False
        self.drain_lock: asyncio.Lock = asyncio.Lock()

        # For exceptions, we try and avoid catch-all blocks. Instead we catch only the exceptions we expect.
        # Exception hierarchy: https://docs.python.org/3/library/exceptions.html#exception-hierarchy

    @staticmethod
    def _validate_client_args(
        smsc_host: str,
        smsc_port: int,
        system_id: str,
        password: str,
        broker: the_broker.BaseBroker,
        client_id: typing.Union[None, str],
        system_type: str,
        addr_ton: int,
        addr_npi: int,
        address_range: str,
        interface_version: int,
        enquire_link_interval: float,
        logger: typing.Union[None, logging.Logger],
        codec: typing.Union[None, the_codec.BaseCodec],
        rate_limiter: typing.Union[None, ratelimiter.BaseRateLimiter],
        hook: typing.Union[None, hooks.BaseHook],
        sequence_generator: typing.Union[None, sequence.BaseSequenceGenerator],
        throttle_handler: typing.Union[None, throttle.BaseThrottleHandler],
        correlation_handler: typing.Union[None, correlater.BaseCorrelater],
        drain_duration: float,
        socket_timeout: float,
    ) -> None:
        """
        Checks that the arguments to `naz.Client` are okay.
        It raises an Exception that comprises of a list of Exceptions
        """
        errors: typing.List[ValueError] = []
        if not isinstance(smsc_host, str):
            errors.append(
                ValueError(
                    "`smsc_host` should be of type:: `str` You entered: {0}".format(type(smsc_host))
                )
            )
        if not isinstance(smsc_port, int):
            errors.append(
                ValueError(
                    "`smsc_port` should be of type:: `int` You entered: {0}".format(type(smsc_port))
                )
            )
        if not isinstance(system_id, str):
            errors.append(
                ValueError(
                    "`system_id` should be of type:: `str` You entered: {0}".format(type(system_id))
                )
            )
        if not isinstance(password, str):
            errors.append(
                ValueError(
                    "`password` should be of type:: `str` You entered: {0}".format(type(password))
                )
            )
        if not isinstance(broker, the_broker.BaseBroker):
            errors.append(
                ValueError(
                    "`broker` should be of type:: `naz.broker.BaseBroker` You entered: {0}".format(
                        type(broker)
                    )
                )
            )
        if not isinstance(client_id, (type(None), str)):
            errors.append(
                ValueError(
                    "`client_id` should be of type:: `None` or `str` You entered: {0}".format(
                        type(client_id)
                    )
                )
            )
        if not isinstance(system_type, str):
            errors.append(
                ValueError(
                    "`system_type` should be of type:: `str` You entered: {0}".format(
                        type(system_type)
                    )
                )
            )
        if not isinstance(addr_ton, int):
            errors.append(
                ValueError(
                    "`addr_ton` should be of type:: `int` You entered: {0}".format(type(addr_ton))
                )
            )
        if not isinstance(addr_npi, int):
            errors.append(
                ValueError(
                    "`addr_npi` should be of type:: `int` You entered: {0}".format(type(addr_npi))
                )
            )
        if not isinstance(address_range, str):
            errors.append(
                ValueError(
                    "`address_range` should be of type:: `str` You entered: {0}".format(
                        type(address_range)
                    )
                )
            )
        if not isinstance(interface_version, int):
            errors.append(
                ValueError(
                    "`interface_version` should be of type:: `int` You entered: {0}".format(
                        type(interface_version)
                    )
                )
            )
        if not isinstance(enquire_link_interval, float):
            errors.append(
                ValueError(
                    "`enquire_link_interval` should be of type:: `float` You entered: {0}".format(
                        type(enquire_link_interval)
                    )
                )
            )
        if not isinstance(logger, (type(None), logging.Logger)):
            errors.append(
                ValueError(
                    "`logger` should be of type:: `None` or `logging.Logger` You entered: {0}".format(
                        type(logger)
                    )
                )
            )
        if not isinstance(codec, (type(None), the_codec.BaseCodec)):
            errors.append(
                ValueError(
                    "`codec` should be of type:: `None` or `naz.codec.BaseCodec` You entered: {0}".format(
                        type(codec)
                    )
                )
            )
        if not isinstance(rate_limiter, (type(None), ratelimiter.BaseRateLimiter)):
            errors.append(
                ValueError(
                    "`rate_limiter` should be of type:: `None` or `naz.ratelimiter.BaseRateLimiter` You entered: {0}".format(
                        type(rate_limiter)
                    )
                )
            )
        if not isinstance(hook, (type(None), hooks.BaseHook)):
            errors.append(
                ValueError(
                    "`hook` should be of type:: `None` or `naz.hooks.BaseHook` You entered: {0}".format(
                        type(hook)
                    )
                )
            )
        if not isinstance(sequence_generator, (type(None), sequence.BaseSequenceGenerator)):
            errors.append(
                ValueError(
                    "`sequence_generator` should be of type:: `None` or `naz.sequence.BaseSequenceGenerator` You entered: {0}".format(
                        type(sequence_generator)
                    )
                )
            )
        if not isinstance(throttle_handler, (type(None), throttle.BaseThrottleHandler)):
            errors.append(
                ValueError(
                    "`throttle_handler` should be of type:: `None` or `naz.throttle.BaseThrottleHandler` You entered: {0}".format(
                        type(throttle_handler)
                    )
                )
            )
        if not isinstance(correlation_handler, (type(None), correlater.BaseCorrelater)):
            errors.append(
                ValueError(
                    "`correlation_handler` should be of type:: `None` or `naz.correlater.BaseCorrelater` You entered: {0}".format(
                        type(correlation_handler)
                    )
                )
            )
        if not isinstance(drain_duration, float):
            errors.append(
                ValueError(
                    "`drain_duration` should be of type:: `float` You entered: {0}".format(
                        type(drain_duration)
                    )
                )
            )
        if not isinstance(socket_timeout, float):
            errors.append(
                ValueError(
                    "`socket_timeout` should be of type:: `float` You entered: {0}".format(
                        type(socket_timeout)
                    )
                )
            )
        if len(errors):
            raise NazClientError(errors)

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

        raise ValueError("That encoding: `{0}` is not recognised.".format(encoding))

    def _search_by_command_id_code(self, command_id_code: int) -> typing.Union[None, str]:
        for key, val in self.command_ids.items():
            if isinstance(val, list):
                __range = range(val[0], val[1] + 1)
                if command_id_code in __range:
                    return key
            else:
                if val == command_id_code:
                    return key
        return None

    @staticmethod
    def _search_by_command_status_value(
        command_status_value: int,
    ) -> typing.Union[None, CommandStatus]:
        # TODO: find a cheaper(better) way of doing this
        for key, val in SmppCommandStatus.__dict__.items():
            if not key.startswith("__"):
                if isinstance(val.value, list):
                    __range = range(val.value[0], val.value[1] + 1)
                    if command_status_value in __range:
                        return val
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

    def _msg_to_log(self, msg: bytes) -> str:
        """
        returns decoded string from bytes with any password removed.
        the returned string is safe to log.
        """
        log_msg = "unable to decode msg"
        try:
            log_msg = msg.decode("ascii")
            if self.password in log_msg:
                # do not log password, redact it from logs.
                log_msg = log_msg.replace(self.password, "{REDACTED}")
        except (UnicodeDecodeError, UnicodeError) as e:
            # in future we may want to do something custom
            _ = e
        except Exception as e:
            _ = e
        return log_msg

    async def connect(self, log_id: str = "") -> None:
        """
        make a network connection to SMSC server.
        """
        log_id = (
            log_id
            if log_id
            else "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
        )
        try:
            self._log(
                logging.INFO, {"event": "naz.Client.connect", "stage": "start", "log_id": log_id}
            )
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.smsc_host, self.smsc_port), timeout=self.socket_timeout
            )
            self.reader = reader
            self.writer = writer
            self._log(
                logging.INFO, {"event": "naz.Client.connect", "stage": "end", "log_id": log_id}
            )
            self.current_session_state = SmppSessionState.OPEN
        except (
            OSError,
            ConnectionError,
            TimeoutError,
            # Note that `asyncio.TimeoutError` is raised with no msg/args. So it will appear in logs as an empty string
            # https://github.com/python/cpython/blob/723f71abf7ab0a7be394f9f7b2daa9ecdf6fb1eb/Lib/asyncio/tasks.py#L490
            asyncio.TimeoutError,
            socket.error,
            socket.herror,
            socket.gaierror,
            socket.timeout,
        ) as e:
            self._log(
                logging.ERROR,
                {"event": "naz.Client.connect", "stage": "end", "log_id": log_id, "error": str(e)},
            )

    async def tranceiver_bind(self, log_id: str = "") -> None:
        """
        send a BIND_TRANSCEIVER pdu to SMSC.
        """
        smpp_command = SmppCommand.BIND_TRANSCEIVER
        if log_id == "":
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
            # system_id is a C-Octet string, which is a series of ASCII characters terminated with the NULL character.
            # see; section 3.1 of SMPP spec
            # Thus we need to encode C-Octet strings as ascii and also terminate them with NULL char(chr(0).encode("ascii"))
            + self.system_id.encode("ascii")
            + chr(0).encode("ascii")
            + self.password.encode("ascii")
            + chr(0).encode("ascii")
            + self.system_type.encode("ascii")
            + chr(0).encode("ascii")
            + struct.pack(">B", self.interface_version)  # unsigned Int, 1octet
            + struct.pack(">B", self.addr_ton)
            + struct.pack(">B", self.addr_npi)
            + self.address_range.encode("ascii")
            + chr(0).encode("ascii")
        )

        # header
        command_length = self._header_pdu_length + len(body)  # 16 is for headers
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
                smpp_command=smpp_command,
                sequence_number=sequence_number,
                log_id=log_id,
                hook_metadata="",
            ),
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

        header = struct.pack(
            ">IIII", command_length, command_id, command_status, sequence_number
        )  # unsigned Int, 4octet
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

    async def enquire_link(self, TESTING: bool = False) -> typing.Union[None, bytes]:
        """
        send an ENQUIRE_LINK pdu to SMSC.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        # sleep during startup so that `naz` can have had time to connect & bind
        # we rely on `enquire_link` to kick on `re_establish_conn_bind`
        while self.current_session_state != SmppSessionState.BOUND_TRX:
            retry_after = self.socket_timeout
            self._log(
                logging.DEBUG,
                {
                    "event": "naz.Client.enquire_link",
                    "stage": "start",
                    "current_session_state": self.current_session_state,
                    "state": "awaiting naz to change session state to `BOUND_TRX`. sleeping for {0:.2f} seconds".format(
                        retry_after
                    ),
                },
            )
            await asyncio.sleep(retry_after)
            if TESTING:
                return None

        smpp_command = SmppCommand.ENQUIRE_LINK
        while True:
            log_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=17))
            self._log(
                logging.DEBUG,
                {
                    "event": "naz.Client.enquire_link",
                    "stage": "start",
                    "log_id": log_id,
                    "smpp_command": smpp_command,
                },
            )
            if self.SHOULD_SHUT_DOWN:
                self._log(
                    logging.DEBUG,
                    {
                        "event": "naz.Client.enquire_link",
                        "stage": "end",
                        "state": "client is shutdown",
                    },
                )
                return None

            # body
            body = b""

            # header
            command_length = self._header_pdu_length + len(body)  # 16 is for headers
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
                    smpp_command=smpp_command,
                    sequence_number=sequence_number,
                    log_id=log_id,
                    hook_metadata="",
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
            # dont queue enquire_link in SimpleBroker since we dont want it to be behind 10k msgs etc
            await self.send_data(smpp_command=smpp_command, msg=full_pdu, log_id=log_id)
            self._log(
                logging.DEBUG,
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
            logging.DEBUG,
            {
                "event": "naz.Client.enquire_link_resp",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )
        try:
            await self.broker.enqueue(
                protocol.EnquireLinkResp(
                    version=self.naz_message_protocol_version,
                    smpp_command=smpp_command,
                    log_id=log_id,
                    sequence_number=sequence_number,
                )
            )
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
            logging.DEBUG,
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
        command_length = self._header_pdu_length + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = SmppCommandStatus.ESME_ROK.value
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        # dont queue unbind_resp in SimpleBroker since we dont want it to be behind 10k msgs etc
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

        try:
            await self.broker.enqueue(
                protocol.DeliverSmResp(
                    version=self.naz_message_protocol_version,
                    smpp_command=smpp_command,
                    log_id=log_id,
                    message_id="",
                    sequence_number=sequence_number,
                )
            )
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
    async def send_message(self, proto_msg: protocol.SubmitSM) -> None:
        """
        Sends a message/SUBMIT_SM to SMSC.
        That message will get enqueued to :attr:`broker <Client.broker>` and later on sent to SMSC.

        Parameters:
            proto_msg: the message to send to SMSC.
                       Has to be a class instance of :class:`naz.protocol.SubmitSM <naz.protocol.SubmitSM>`

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
        if not isinstance(proto_msg, protocol.SubmitSM):
            raise ValueError(
                "`proto_msg` should be of type:: `naz.protocol.SubmitSM` You entered: {0}".format(
                    type(proto_msg)
                )
            )
        smpp_command = proto_msg.smpp_command
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.send_message",
                "stage": "start",
                "log_id": proto_msg.log_id,
                "smpp_command": smpp_command,
            },
        )
        try:
            await self.broker.enqueue(proto_msg)
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.send_message",
                    "stage": "end",
                    "error": str(e),
                    "log_id": proto_msg.log_id,
                    "smpp_command": smpp_command,
                    "short_message": proto_msg.short_message,
                },
            )
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.send_message",
                "stage": "end",
                "log_id": proto_msg.log_id,
                "smpp_command": smpp_command,
            },
        )

    async def _build_enquire_link_resp_pdu(self, proto_msg: protocol.EnquireLinkResp) -> bytes:
        smpp_command = SmppCommand.ENQUIRE_LINK_RESP
        log_id = proto_msg.log_id
        sequence_number = proto_msg.sequence_number
        self._log(
            logging.DEBUG,
            {
                "event": "naz.Client._build_enquire_link_resp_pdu",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

        # body
        body = b""

        # header
        command_length = self._header_pdu_length + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = SmppCommandStatus.ESME_ROK.value
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        self._log(
            logging.DEBUG,
            {
                "event": "naz.Client._build_enquire_link_resp_pdu",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )
        return full_pdu

    async def _build_deliver_sm_pdu(self, proto_msg: protocol.DeliverSmResp) -> bytes:
        smpp_command = SmppCommand.DELIVER_SM_RESP
        log_id = proto_msg.log_id
        message_id = proto_msg.message_id
        sequence_number = proto_msg.sequence_number
        self._log(
            logging.INFO,
            {
                "event": "naz.Client._build_deliver_sm_pdu",
                "stage": "start",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )

        # body
        body = b""
        message_id = ""
        body = body + message_id.encode("ascii") + chr(0).encode("ascii")

        # header
        command_length = self._header_pdu_length + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        command_status = SmppCommandStatus.ESME_ROK.value
        sequence_number = sequence_number
        header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

        full_pdu = header + body
        self._log(
            logging.INFO,
            {
                "event": "naz.Client._build_deliver_sm_pdu",
                "stage": "end",
                "log_id": log_id,
                "smpp_command": smpp_command,
            },
        )
        return full_pdu

    async def _build_submit_sm_pdu(self, proto_msg: protocol.SubmitSM) -> bytes:
        """
        builds a SUBMIT_SM pdu.

        Parameters:
            proto_msg: an instance of `naz.protocol.SubmitSM`
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
        log_id = proto_msg.log_id
        hook_metadata = proto_msg.hook_metadata
        short_message = proto_msg.short_message
        source_addr = proto_msg.source_addr
        destination_addr = proto_msg.destination_addr
        service_type = proto_msg.service_type
        source_addr_ton = proto_msg.source_addr_ton
        source_addr_npi = proto_msg.source_addr_npi
        dest_addr_ton = proto_msg.dest_addr_ton
        dest_addr_npi = proto_msg.dest_addr_npi
        esm_class = proto_msg.esm_class
        protocol_id = proto_msg.protocol_id
        priority_flag = proto_msg.priority_flag
        schedule_delivery_time = proto_msg.schedule_delivery_time
        validity_period = proto_msg.validity_period
        registered_delivery = proto_msg.registered_delivery
        replace_if_present_flag = proto_msg.replace_if_present_flag
        sm_default_msg_id = proto_msg.sm_default_msg_id

        self._log(
            logging.DEBUG,
            {
                "event": "naz.Client._build_submit_sm_pdu",
                "stage": "start",
                "log_id": log_id,
                "short_message": short_message,
                "source_addr": source_addr,
                "destination_addr": destination_addr,
                "smpp_command": smpp_command,
            },
        )
        encoded_short_message = self.codec.encode(short_message)
        sm_length = len(encoded_short_message)

        # body
        # SUBMIT_SM KKKK
        body = b""
        body = (
            body
            + service_type.encode("ascii")
            + chr(0).encode("ascii")
            + struct.pack(">B", source_addr_ton)  # unsigned Int, 1octet
            + struct.pack(">B", source_addr_npi)
            + source_addr.encode("ascii")
            + chr(0).encode("ascii")
            + struct.pack(">B", dest_addr_ton)
            + struct.pack(">B", dest_addr_npi)
            + destination_addr.encode("ascii")
            + chr(0).encode("ascii")
            + struct.pack(">B", esm_class)
            + struct.pack(">B", protocol_id)
            + struct.pack(">B", priority_flag)
            + schedule_delivery_time.encode("ascii")
            + chr(0).encode("ascii")
            + validity_period.encode("ascii")
            + chr(0).encode("ascii")
            + struct.pack(">B", registered_delivery)
            + struct.pack(">B", replace_if_present_flag)
            + struct.pack(">B", self.data_coding)
            + struct.pack(">B", sm_default_msg_id)
            + struct.pack(">B", sm_length)
            + self.codec.encode(short_message)
        )

        # header
        command_length = self._header_pdu_length + len(body)  # 16 is for headers
        command_id = self.command_ids[smpp_command]
        # the status for success see section 5.1.3
        command_status = 0x00000000  # not used for `submit_sm`
        try:
            sequence_number = self.sequence_generator.next_sequence()
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client._build_submit_sm_pdu",
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
                smpp_command=smpp_command,
                sequence_number=sequence_number,
                log_id=log_id,
                hook_metadata=hook_metadata,
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client._build_submit_sm_pdu",
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
            logging.DEBUG,
            {
                "event": "naz.Client._build_submit_sm_pdu",
                "stage": "end",
                "log_id": log_id,
                "short_message": short_message,
                "source_addr": source_addr,
                "destination_addr": destination_addr,
                "smpp_command": smpp_command,
            },
        )
        return full_pdu

    async def re_establish_conn_bind(
        self, smpp_command: str, log_id: str, TESTING: bool = False
    ) -> None:
        """
        Called if connection is lost. It reconnects & rebinds to SMSC.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        # the only reason this method is called is because connection has closed.
        # so lets set the session state to reflect that fact
        self.current_session_state = SmppSessionState.CLOSED
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.re_establish_conn_bind",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "connection_lost": self.writer.transport.is_closing() if self.writer else True,
            },
        )
        if self.SHOULD_SHUT_DOWN:
            self._log(
                logging.DEBUG,
                {
                    "event": "naz.Client.re_establish_conn_bind",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "cleanly shutting down client.",
                },
            )
            return None

        # 1. re-connect
        # 2. re-bind
        await self.connect(log_id=log_id)
        if self.current_session_state == SmppSessionState.OPEN:
            # state can only be open if `client.connect` succeded
            await self.tranceiver_bind(log_id=log_id)
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.re_establish_conn_bind",
                "stage": "end",
                "smpp_command": smpp_command,
                "log_id": log_id,
            },
        )
        if TESTING:
            # offer escape hatch for tests to come out of endless loop
            return None

    async def send_data(
        self, smpp_command: str, msg: bytes, log_id: str, hook_metadata: str = ""
    ) -> None:
        """
        Sends PDU's to SMSC over a network connection.
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
        log_msg = self._msg_to_log(msg=msg)
        self._log(
            logging.INFO,
            {
                "event": "naz.Client.send_data",
                "stage": "start",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "msg": log_msg,
                "connection_lost": self.writer.transport.is_closing() if self.writer else True,
            },
        )

        # check session state to see if we can send messages.
        # see section 2.3 of SMPP spec document v3.4
        if self.current_session_state == SmppSessionState.CLOSED:
            error_msg = "smpp_command `{0}` cannot be sent to SMSC when the client session state is `{1}`".format(
                smpp_command, self.current_session_state
            )
            self._log(
                logging.ERROR,
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
            return None
        elif (
            self.current_session_state == SmppSessionState.OPEN
            and smpp_command == SmppCommand.ENQUIRE_LINK
        ):
            # If the connection to  SMSC is broken, we need to call `Client.re_establish_conn_bind`.
            # That method is only called by `Client.send_data`. Thus someone has to call `Client.send_data` even
            # when the connection is broken in order for it to call `re_establish_conn_bind` and restore connection
            # That someone is `enquire_link`. This is why in this block we have `enquire_link` and logging it at DEBUG level
            # and we do not return
            error_msg = "smpp_command `{0}` cannot be sent to SMSC when the client session state is `{1}`".format(
                smpp_command, self.current_session_state
            )
            self._log(
                logging.DEBUG,
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
            # do not raise or return
        elif self.current_session_state == SmppSessionState.OPEN and smpp_command not in [
            SmppCommand.BIND_TRANSMITTER,
            SmppCommand.BIND_RECEIVER,
            SmppCommand.BIND_TRANSCEIVER,
        ]:
            # only the smpp_command's listed above are allowed by SMPP spec to be sent
            # if current_session_state == SmppSessionState.OPEN
            error_msg = "smpp_command `{0}` cannot be sent to SMSC when the client session state is `{1}`".format(
                smpp_command, self.current_session_state
            )
            self._log(
                logging.ERROR,
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
            # do not raise, we do not want naz-cli to exit
            return None

        if (self.writer is None) or self.writer.transport.is_closing():
            await self.re_establish_conn_bind(smpp_command=smpp_command, log_id=log_id)

        try:
            # call user's hook for requests
            await self.hook.to_smsc(
                smpp_command=smpp_command, log_id=log_id, hook_metadata=hook_metadata, pdu=msg
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.send_data",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "to_smsc hook error",
                    "error": str(e),
                },
            )

        try:
            if typing.TYPE_CHECKING:
                # make mypy happy; https://github.com/python/mypy/issues/4805
                assert isinstance(self.writer, asyncio.streams.StreamWriter)

            # We use writer.drain() which is a flow control method that interacts with the IO write buffer.
            # When the size of the buffer reaches the high watermark,
            # drain blocks until the size of the buffer is drained down to the low watermark and writing can be resumed.
            # When there is nothing to wait for, the drain() returns immediately.
            # ref: https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.drain
            self.writer.write(msg)
            async with self.drain_lock:
                # see: https://github.com/komuw/naz/issues/114
                await self.writer.drain()
            if smpp_command == SmppCommand.BIND_TRANSCEIVER:
                # if we have successfully sent a bind_transceiver request, we can set session state to `BOUND_TRX`
                # Ideally, you should only set state to `BOUND_TRX` once SMSC sends back a successful `BIND_TRANSCEIVER_RESP`
                # However, an SMSC may fail to do so. This is especially true when sending `re_establish_conn_bind`
                # hack!! bad!!
                # TODO: fix this
                self.current_session_state = SmppSessionState.BOUND_TRX
        except (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            socket.error,
            socket.herror,
            socket.gaierror,
            socket.timeout,
        ) as e:
            # https://docs.python.org/3/library/socket.html#exceptions
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.send_data",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "unable to write to SMSC",
                    "error": str(e),
                },
            )

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

    async def dequeue_messages(
        self, TESTING: bool = False
    ) -> typing.Union[protocol.Message, typing.Dict[typing.Any, typing.Any]]:
        """
        In a loop; dequeues items from the :attr:`broker <Client.broker>` and sends them to SMSC.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        dequeue_retry_count = 0
        while True:
            self._log(logging.INFO, {"event": "naz.Client.dequeue_messages", "stage": "start"})
            if self.SHOULD_SHUT_DOWN:
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.dequeue_messages",
                        "stage": "end",
                        "state": "cleanly shutting down client.",
                    },
                )
                return {"shutdown": "shutdown"}

            while self.current_session_state != SmppSessionState.BOUND_TRX:
                # If the connection to SMSC is broken, there's no need to try and send messages
                # sleep and wait for `Client.re_establish_conn_bind` to do its thing.
                # this same thing cannot be done for `enquire_link` since we rely on it to kick on `re_establish_conn_bind`
                retry_after = self.socket_timeout
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.dequeue_messages",
                        "stage": "start",
                        "current_session_state": self.current_session_state,
                        "state": "awaiting naz to change session state to `BOUND_TRX`. sleeping for {0:.2f} seconds".format(
                            retry_after
                        ),
                    },
                )
                await asyncio.sleep(retry_after)
                if TESTING:
                    return {"state": "awaiting naz to change session state to `BOUND_TRX`"}

            # TODO: there are so many try-except classes in this func.
            # do something about that.
            try:
                # check with throttle handler
                send_request = await self.throttle_handler.allow_request()
            except Exception as e:
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.dequeue_messages",
                        "stage": "end",
                        "state": "dequeue_messages error",
                        "error": str(e),
                    },
                )
                continue
            if send_request:
                try:
                    # rate limit ourselves
                    await self.rate_limiter.limit()
                except Exception as e:
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.dequeue_messages",
                            "stage": "end",
                            "state": "dequeue_messages error",
                            "error": str(e),
                        },
                    )

                try:
                    proto_msg = await self.broker.dequeue()
                except Exception as e:
                    dequeue_retry_count += 1
                    poll_queue_interval = self._retry_after(dequeue_retry_count)
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.dequeue_messages",
                            "stage": "end",
                            "state": "dequeue_messages error. sleeping for {0:.2f} seconds".format(
                                poll_queue_interval
                            ),
                            "dequeue_retry_count": dequeue_retry_count,
                            "error": str(e),
                        },
                    )
                    if self.SHOULD_SHUT_DOWN:
                        return {"shutdown": "shutdown"}
                    if TESTING:
                        # offer escape hatch for tests to come out of endless loop
                        return {"broker_error": "broker_error"}
                    await asyncio.sleep(poll_queue_interval)
                    continue

                # we didn't fail to dequeue a message
                dequeue_retry_count = 0
                try:
                    log_id = proto_msg.log_id
                    proto_msg.version  # version is a required field
                    smpp_command = proto_msg.smpp_command
                    hook_metadata = proto_msg.hook_metadata
                    if isinstance(proto_msg, protocol.SubmitSM):
                        full_pdu = await self._build_submit_sm_pdu(proto_msg)
                    elif isinstance(proto_msg, protocol.DeliverSmResp):
                        full_pdu = await self._build_deliver_sm_pdu(proto_msg)
                    elif isinstance(proto_msg, protocol.EnquireLinkResp):
                        full_pdu = await self._build_enquire_link_resp_pdu(proto_msg)
                    else:
                        raise ValueError(
                            "The protocol message `{0}` is not recognised by naz.".format(
                                type(proto_msg)
                            )
                        )
                except Exception as e:
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.dequeue_messages",
                            "stage": "end",
                            "state": "dequeue_messages error",
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
                        "event": "naz.Client.dequeue_messages",
                        "stage": "end",
                        "log_id": log_id,
                        "smpp_command": smpp_command,
                        "send_request": send_request,
                    },
                )
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return proto_msg
            else:
                # throttle_handler didn't allow us to send request.
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.dequeue_messages",
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
                            "event": "naz.Client.dequeue_messages",
                            "stage": "end",
                            "state": "dequeue_messages error",
                            "error": str(e),
                        },
                    )
                    continue
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return {"throttle_handler_denied_request": "throttle_handler_denied_request"}
                continue

    async def receive_data(self, TESTING: bool = False) -> typing.Union[None, bytes]:
        """
        In a loop; read bytes from the network connected to SMSC and hand them over to the :func:`_parse_response_pdu <Client._parse_response_pdu>` method for parsing.

        Parameters:
            TESTING: indicates whether this method is been called while running tests.
        """
        retry_count = 0
        while True:
            self._log(logging.INFO, {"event": "naz.Client.receive_data", "stage": "start"})
            if self.SHOULD_SHUT_DOWN:
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.receive_data",
                        "stage": "end",
                        "state": "cleanly shutting down client.",
                    },
                )
                return None
            if self.current_session_state != SmppSessionState.BOUND_TRX:
                retry_after = self.socket_timeout
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.receive_data",
                        "stage": "end",
                        "state": "naz is yet to bind to SMSC. sleeping for {0:.2f} seconds".format(
                            retry_after
                        ),
                    },
                )
                await asyncio.sleep(retry_after)
                await self.re_establish_conn_bind(smpp_command="", log_id="")
                continue

            header_data = b""
            try:
                if typing.TYPE_CHECKING:
                    # make mypy happy; https://github.com/python/mypy/issues/4805
                    assert isinstance(self.reader, asyncio.streams.StreamReader)

                # `client.reader` and `client.writer` should not have timeouts since they are non-blocking
                # https://github.com/komuw/naz/issues/116
                header_data = await self.reader.readexactly(self._header_pdu_length)
            except asyncio.IncompleteReadError as e:
                # see: https://github.com/komuw/naz/issues/135
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.receive_data",
                        "stage": "end",
                        "state": "unable to read exactly {0}bytes of smpp header.".format(
                            self._header_pdu_length
                        ),
                        "error": str(e),
                    },
                )
                # close connection. it will be automatically reconnected later
                await self._unbind_and_disconnect()
                if TESTING:
                    # offer escape hatch for tests to come out of endless loop
                    return header_data
            except (
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
                socket.error,
                socket.herror,
                socket.gaierror,
                socket.timeout,
            ) as e:
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.receive_data",
                        "stage": "end",
                        "state": "unable to read from SMSC",
                        "error": str(e),
                    },
                )

            if header_data == b"":
                retry_count += 1
                poll_read_interval = self._retry_after(retry_count)
                self._log(
                    logging.INFO,
                    {
                        "event": "naz.Client.receive_data",
                        "stage": "start",
                        "state": "no data received from SMSC. sleeping for {0:.2f} seconds".format(
                            poll_read_interval
                        ),
                        "retry_count": retry_count,
                    },
                )
                if self.SHOULD_SHUT_DOWN:
                    return None
                await asyncio.sleep(poll_read_interval)
                continue
            else:
                # we didn't fail to read from SMSC
                retry_count = 0

            # first 4bytes of header are the command_length
            total_pdu_length = struct.unpack(">I", header_data[:4])[0]
            MSGLEN = total_pdu_length - self._header_pdu_length
            chunks = []
            bytes_recd = 0
            while bytes_recd < MSGLEN:
                chunk = b""
                try:
                    if typing.TYPE_CHECKING:
                        # make mypy happy; https://github.com/python/mypy/issues/4805
                        assert isinstance(self.reader, asyncio.streams.StreamReader)

                    chunk = await self.reader.read(min(MSGLEN - bytes_recd, 2048))
                    if chunk == b"":
                        # TODO: maybe we also need todo; `self.writer=None`
                        # so that the `re_establish_conn_bind` mechanism can kick in.
                        raise ConnectionError("socket connection broken")
                except (
                    ConnectionError,
                    TimeoutError,
                    asyncio.TimeoutError,
                    socket.error,
                    socket.herror,
                    socket.gaierror,
                    socket.timeout,
                ) as e:
                    self._log(
                        logging.ERROR,
                        {
                            "event": "naz.Client.receive_data",
                            "stage": "end",
                            "state": "unable to read from SMSC",
                            "error": str(e),
                        },
                    )
                    if self.SHOULD_SHUT_DOWN:
                        return None

                    _read_smsc_interval = 62.00
                    self._log(
                        logging.DEBUG,
                        {
                            "event": "naz.Client.receive_data",
                            "stage": "end",
                            "state": "unable to read from SMSC. sleeping for {0:.2f} seconds".format(
                                _read_smsc_interval
                            ),
                            "error": str(e),
                        },
                    )
                    await asyncio.sleep(_read_smsc_interval)
                    continue  # important so that we do not hit the bug: issues/135
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)

            full_pdu_data = header_data + b"".join(chunks)
            self._log(
                logging.DEBUG,
                {
                    "event": "naz.Client.receive_data",
                    "stage": "end",
                    "full_pdu_data": self._msg_to_log(msg=full_pdu_data),
                },
            )
            await self._parse_response_pdu(full_pdu_data)
            self._log(logging.INFO, {"event": "naz.Client.receive_data", "stage": "end"})
            if TESTING:
                # offer escape hatch for tests to come out of endless loop
                return full_pdu_data

    async def _parse_response_pdu(self, pdu: bytes) -> None:
        """
        Take the bytes that have been read from network and parse them into their corresponding PDU.
        The resulting PDU is then handed over to :func:`command_handlers <Client.command_handlers>`

        Parameters:
            pdu: PDU in bytes, that have been read from network
        """
        log_pdu = self._msg_to_log(msg=pdu)
        self._log(
            logging.DEBUG,
            {"event": "naz.Client._parse_response_pdu", "stage": "start", "pdu": log_pdu},
        )

        header_data = pdu[: self._header_pdu_length]
        body_data = pdu[self._header_pdu_length :]
        command_id_header_data = header_data[4:8]
        command_status_header_data = header_data[8:12]
        sequence_number_header_data = header_data[12:16]

        try:
            command_id = struct.unpack(">I", command_id_header_data)[0]
            command_status = struct.unpack(">I", command_status_header_data)[0]
            sequence_number = struct.unpack(">I", sequence_number_header_data)[0]
        except (struct.error, IndexError) as e:
            # see: https://github.com/komuw/naz/issues/135
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client._parse_response_pdu",
                    "stage": "end",
                    "state": "parse SMSC response error.",
                    "error": str(e),
                    "pdu": log_pdu,
                },
            )
            # close connection
            await self._unbind_and_disconnect()
            return None

        smpp_command = self._search_by_command_id_code(command_id)
        if not smpp_command:
            err = ValueError("command_id:{0} is unknown.".format(command_id))
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client._parse_response_pdu",
                    "stage": "end",
                    "state": "command_id:{0} is unknown.".format(command_id),
                    "error": str(err),
                },
            )
            return None

        # get associated user supplied log_id if any
        try:
            log_id, hook_metadata = await self.correlation_handler.get(
                smpp_command=smpp_command, sequence_number=sequence_number
            )
        except Exception as e:
            log_id, hook_metadata = "", ""
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client._parse_response_pdu",
                    "stage": "start",
                    "log_id": log_id,
                    "state": "correlater get error",
                    "error": str(e),
                },
            )

        await self.command_handlers(
            pdu=pdu,
            body_data=body_data,
            smpp_command=smpp_command,
            command_status_value=command_status,
            sequence_number=sequence_number,
            log_id=log_id,
            hook_metadata=hook_metadata,
        )
        self._log(
            logging.DEBUG,
            {
                "event": "naz.Client._parse_response_pdu",
                "stage": "end",
                "smpp_command": smpp_command,
                "log_id": log_id,
                "command_status": command_status,
            },
        )

    async def command_handlers(
        self,
        pdu: bytes,
        body_data: bytes,
        smpp_command: str,
        command_status_value: int,
        sequence_number: int,
        log_id: str,
        hook_metadata: str,
    ) -> None:
        """
        This routes the various different SMPP PDU to their respective handlers.

        Parameters:
            pdu: the full PDU as received from SMSC
            body_data: PDU body as received from SMSC
            smpp_command: type of PDU been received. eg bind_transceiver_resp
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
                    "event": "naz.Client.command_handlers",
                    "stage": "start",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "error": "command_status: `{0}` is unknown.".format(command_status_value),
                },
            )
            return None
        elif commandStatus.value != SmppCommandStatus.ESME_ROK.value:
            # we got an error from SMSC
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.command_handlers",
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
                    "event": "naz.Client.command_handlers",
                    "stage": "start",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "command_status": commandStatus.value,
                    "state": commandStatus.description,
                },
            )

        try:
            # call throttling handler
            if commandStatus.value in [
                SmppCommandStatus.ESME_RTHROTTLED.value,
                SmppCommandStatus.ESME_RMSGQFUL.value,
            ]:
                await self.throttle_handler.throttled()
            else:
                await self.throttle_handler.not_throttled()
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.command_handlers",
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
            try:
                # the body of this only has `message_id` which is a C-Octet String of variable length upto 65 octets.
                # This field contains the SMSC message_id of the submitted message.
                # It may be used at a later stage to query the status of a message, cancel
                # or replace the message.
                _message_id = body_data.replace(chr(0).encode("ascii"), b"")
                smsc_message_id = _message_id.decode("ascii")
                await self.correlation_handler.put(
                    smpp_command=smpp_command,
                    sequence_number=sequence_number,
                    smsc_message_id=smsc_message_id,
                    log_id=log_id,
                    hook_metadata=hook_metadata,
                )
            except Exception as e:
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.command_handlers",
                        "stage": "end",
                        "smpp_command": smpp_command,
                        "log_id": log_id,
                        "state": "correlater put error",
                        "error": str(e),
                    },
                )
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

            await self.deliver_sm_resp(sequence_number=sequence_number)
            try:
                # get associated user supplied log_id if any
                target_tag = struct.pack(
                    ">H", SmppOptionalTag.receipted_message_id
                )  # unsigned Int, 2octet
                if target_tag in body_data:
                    # the PDU contains a `receipted_message_id` TLV optional tag
                    position_of_target_tag = body_data.find(target_tag)
                    # since a tag is 2 integer in size lets skip one more.
                    end_of_target_tag = position_of_target_tag + 1
                    # since after a tag, comes a tag_length which is 2 integer in size
                    # lets also skip that
                    end_of_target_tag_length = end_of_target_tag + 2
                    end_of_target_tag_length = (
                        end_of_target_tag_length + 1
                    )  # because of c-octet string null termination
                    # tag_value is of size 1 - 65
                    end_of_tag_value = end_of_target_tag_length + 65
                    tag_value = body_data[end_of_target_tag_length:end_of_tag_value]
                    _tag_value = tag_value.replace(
                        chr(0).encode("ascii"), b""
                    )  # change variable names to make mypy happy
                    t_value = _tag_value.decode("ascii")
                    log_id, hook_metadata = await self.correlation_handler.get(
                        smpp_command=smpp_command,
                        sequence_number=sequence_number,
                        smsc_message_id=t_value,
                    )
            except Exception as e:
                log_id, hook_metadata = "", ""
                self._log(
                    logging.ERROR,
                    {
                        "event": "naz.Client.command_handlers",
                        "stage": "start",
                        "log_id": log_id,
                        "state": "correlater get error",
                        "error": str(e),
                    },
                )
        elif smpp_command == SmppCommand.ENQUIRE_LINK:
            # we have to handle this. we have to return enquire_link_resp
            # it has no body
            await self.enquire_link_resp(sequence_number=sequence_number)
        else:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.command_handlers",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "command_status": commandStatus.code,
                    "state": commandStatus.description,
                    "error": "the smpp_command: `{0}` has not been implemented in naz. please create a github issue".format(
                        smpp_command
                    ),
                },
            )

        try:
            # call user's hook for responses
            # this has to be done last
            await self.hook.from_smsc(
                smpp_command=smpp_command,
                log_id=log_id,
                hook_metadata=hook_metadata,
                status=commandStatus,
                pdu=pdu,
            )
        except Exception as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client.command_handlers",
                    "stage": "end",
                    "smpp_command": smpp_command,
                    "log_id": log_id,
                    "state": "from_smsc hook error",
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
        command_length = self._header_pdu_length + len(body)  # 16 is for headers
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
                smpp_command=smpp_command,
                sequence_number=sequence_number,
                log_id=log_id,
                hook_metadata="",
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
        # dont queue unbind in SimpleBroker since we dont want it to be behind 10k msgs etc
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

    async def shutdown(self) -> None:
        """
        Cleanly shutdown this client.
        """
        self._log(
            logging.INFO,
            {"event": "naz.Client.shutdown", "stage": "start", "state": "intiating shutdown"},
        )
        self.SHOULD_SHUT_DOWN = True

        await self._unbind_and_disconnect()

        # sleep so that client can:
        # - stop consuming from queue
        # - finish sending any SMSes it may have already picked from queue
        # - stop sending `enquire_link` requests
        # - send unbind to SMSC
        await asyncio.sleep(self.drain_duration)  # asyncio.sleep so that we do not block eventloop
        self._log(logging.DEBUG, {"event": "naz.Client.shutdown", "stage": "end"})

    async def _unbind_and_disconnect(self):
        """
        unbind from SMSC and close network connection.
        This is usually done in two situations;
          - when shutting down a naz client
          - if we got into an unrecoverable state and need to start over; issues/135
        """
        self._log(logging.DEBUG, {"event": "naz.Client._unbind_and_disconnect", "stage": "start"})

        if typing.TYPE_CHECKING:
            # make mypy happy; https://github.com/python/mypy/issues/4805
            assert isinstance(self.writer, asyncio.streams.StreamWriter)
            assert isinstance(self.writer.transport, asyncio.transports.Transport)
        try:
            # 1. set buffers to 0
            # 2. unbind
            # 3. drain
            # 4. close connection
            # in that order

            # see: https://github.com/komuw/naz/issues/117
            self.writer.transport.set_write_buffer_limits(0)  # pytype: disable=attribute-error
            # https://github.com/google/pytype/issues/350
            await self.unbind()
            async with self.drain_lock:
                await self.writer.drain()
            self.writer.close()
        except (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            socket.error,
            socket.herror,
            socket.gaierror,
            socket.timeout,
        ) as e:
            self._log(
                logging.ERROR,
                {
                    "event": "naz.Client._unbind_and_disconnect",
                    "stage": "end",
                    "state": "unable to write to SMSC",
                    "error": str(e),
                },
            )
        self._log(logging.DEBUG, {"event": "naz.Client._unbind_and_disconnect", "stage": "end"})


class NazClientError(Exception):
    """
    Error raised when there's an error instantiating a naz Client.
    """

    pass

import abc
import time
import typing
import logging

from . import log


class BaseThrottleHandler(abc.ABC):
    """
    This is the interface that must be implemented to satisfy naz's throttle handling.
    User implementations should inherit this class and
    implement the :func:`throttled <BaseThrottleHandler.throttled>`, :func:`not_throttled <BaseThrottleHandler.not_throttled>`,
    :func:`allow_request <BaseThrottleHandler.allow_request>` and
    :func:`throttle_delay <BaseThrottleHandler.throttle_delay>` methods with the type signatures shown.

    When an SMPP client exceeds it's rate limit, or when the SMSC is under load or for whatever reason;
    The SMSC may decide to start throtlling requests from that particular client.
    When it does so, it replies to the client with a throttling status. Under such conditions, it is important for the client to start
    rate limiting itself. The way naz implements this self imposed self-regulation is via Throttle Handlers.

    The methods in this class are also called when the SMSC is under load and is responding with `ESME_RMSGQFUL`(message queue full) responses
    """

    @abc.abstractmethod
    async def throttled(self) -> None:
        """
        this method will be called by naz everytime we get a throttling response from SMSC.
        """
        raise NotImplementedError("throttled method must be implemented.")

    @abc.abstractmethod
    async def not_throttled(self) -> None:
        """
        this method will be called by naz everytime we get any response from SMSC that is not a throttling response.
        """
        raise NotImplementedError("not_throttled method must be implemented.")

    @abc.abstractmethod
    async def allow_request(self) -> bool:
        """
        this method will be called by naz just before sending a request to SMSC.
        The response from this method will determine wether naz will send the request or not.
        """
        raise NotImplementedError("allow_request method must be implemented.")

    @abc.abstractmethod
    async def throttle_delay(self) -> float:
        """
        if the last :func:`allow_request <BaseThrottleHandler.allow_request>` method call returned False(thus denying sending a request),
        naz will call the throttle_delay method
        to determine how long in seconds to wait before calling allow_request again.
        """
        raise NotImplementedError("throttle_delay method must be implemented.")


class SimpleThrottleHandler(BaseThrottleHandler):
    """
    This is an implementation of BaseThrottleHandler.

    It works by:

    - calculating the percentage of responses from the SMSC that are THROTTLING(or ESME_RMSGQFUL) responses.
    - if that percentage goes above :attr:`deny_request_at <SimpleThrottleHandler.deny_request_at>` percent AND \
    total number of responses from SMSC is greater than :attr:`sample_size <SimpleThrottleHandler.sample_size>` over \
    :attr:`sampling_period <SimpleThrottleHandler.sampling_period>` seconds
    - then deny making anymore requests to SMSC

    """

    def __init__(
        self,
        sampling_period: float = 180.00,
        sample_size: float = 50.00,
        deny_request_at: float = 1.00,
        throttle_wait: float = 3.00,
        logger: typing.Union[None, log.BaseLogger] = None,
    ) -> None:
        """
        Parameters:
            sampling_period: the duration in seconds over which we will calculate the percentage of throttled responses.
            sample_size: the minimum number of responses we should have got from SMSC over :sampling_period duration to enable us make a decision.
            deny_request_at: the percent of throtlled responses above which we will deny naz from sending more requests to SMSC.
            throttle_wait: the time in seconds to wait before calling allow_request after the last allow_request that returned False.
        """
        if not isinstance(sampling_period, float):
            raise ValueError(
                "`sampling_period` should be of type:: `float` You entered: {0}".format(
                    type(sampling_period)
                )
            )
        if not isinstance(sample_size, float):
            raise ValueError(
                "`sample_size` should be of type:: `float` You entered: {0}".format(
                    type(sample_size)
                )
            )
        if not isinstance(deny_request_at, float):
            raise ValueError(
                "`deny_request_at` should be of type:: `float` You entered: {0}".format(
                    type(deny_request_at)
                )
            )
        if not isinstance(throttle_wait, float):
            raise ValueError(
                "`throttle_wait` should be of type:: `float` You entered: {0}".format(
                    type(throttle_wait)
                )
            )
        if not isinstance(logger, (type(None), log.BaseLogger)):
            raise ValueError(
                "`logger` should be of type:: `None` or `naz.log.BaseLogger` You entered: {0}".format(
                    type(logger)
                )
            )

        self.NON_throttle_responses: int = 0
        self.throttle_responses: int = 0
        self.updated_at: float = time.monotonic()

        self.sampling_period: float = sampling_period
        self.sample_size: float = sample_size
        self.deny_request_at: float = deny_request_at
        self.throttle_wait: float = throttle_wait

        if logger is not None:
            self.logger = logger
        else:
            self.logger = log.SimpleLogger("naz.SimpleThrottleHandler")

    @property
    def percent_throttles(self) -> float:
        total_smsc_responses: int = self.NON_throttle_responses + self.throttle_responses
        if total_smsc_responses < self.sample_size:
            # we do not have enough data to make decision, so asssume happy case
            return 0.0
        return round((self.throttle_responses / (total_smsc_responses)) * 100, 2)

    async def allow_request(self) -> bool:
        self.logger.log(
            logging.DEBUG, {"event": "naz.SimpleThrottleHandler.allow_request", "stage": "start"}
        )
        # calculat percentage of throttles before resetting NON_throttle_responses and throttle_responses
        current_percent_throttles: float = self.percent_throttles
        _throttle_responses: int = self.throttle_responses
        _NON_throttle_responses: int = self.NON_throttle_responses

        now: float = time.monotonic()
        time_since_update: float = now - self.updated_at
        if time_since_update > self.sampling_period:
            # we are only interested in percent throttles in buckets of self.sampling_period seconds.
            # so reset values after self.sampling_period seconds.
            self.NON_throttle_responses = 0
            self.throttle_responses = 0
            self.updated_at = now
        if current_percent_throttles > self.deny_request_at:
            self.logger.log(
                logging.INFO,
                {
                    "event": "naz.SimpleThrottleHandler.allow_request",
                    "stage": "end",
                    "percent_throttles": current_percent_throttles,
                    "throttle_responses": _throttle_responses,
                    "NON_throttle_responses": _NON_throttle_responses,
                    "sampling_period": self.sampling_period,
                    "sample_size": self.sample_size,
                    "deny_request_at": self.deny_request_at,
                    "state": "deny_request",
                },
            )
            return False
        self.logger.log(
            logging.DEBUG,
            {
                "event": "naz.SimpleThrottleHandler.allow_request",
                "stage": "end",
                "percent_throttles": current_percent_throttles,
                "throttle_responses": _throttle_responses,
                "NON_throttle_responses": _NON_throttle_responses,
                "sampling_period": self.sampling_period,
                "sample_size": self.sample_size,
                "deny_request_at": self.deny_request_at,
                "state": "allow_request",
            },
        )
        return True

    async def not_throttled(self) -> None:
        self.NON_throttle_responses += 1

    async def throttled(self) -> None:
        self.throttle_responses += 1

    async def throttle_delay(self) -> float:
        # todo: sleep in an exponetial manner upto a maximum then wrap around.
        return self.throttle_wait

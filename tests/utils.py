import asyncio
import logging
from unittest import mock


# capture warnings during test runs
logging.captureWarnings(True)


def AsyncMock(*args, **kwargs):
    """
    see: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    """
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class MockStreamWriter:
    """
    This is a mock of python's StreamWriter;
    https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter
    """

    def __init__(self, _is_closing=False):
        self.transport = self._create_transport(_is_closing=_is_closing)

    async def drain(self):
        pass

    def close(self):
        # when this is called, we set the transport to be in closed/closing state
        self.transport = self._create_transport(_is_closing=True)

    def write(self, data):
        pass

    def write_eof(self):
        pass

    def get_extra_info(self, name, default=None):
        # when this is called, we set the transport to be in open state.
        # this is because this method is called in `naz.Client.connect`
        # so it is the only chance we have of 're-establishing' connection
        self.transport = self._create_transport(_is_closing=False)

        return self.transport

    def _create_transport(self, _is_closing):
        class MockTransport:
            def __init__(self, _is_closing):
                self._is_closing = _is_closing

            def set_write_buffer_limits(self, n):
                pass

            def is_closing(self):
                return self._is_closing

            def settimeout(self, socket_timeout):
                pass

        return MockTransport(_is_closing=_is_closing)


class MockStreamReader:
    """
    This is a mock of python's StreamReader;
    https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamReader
    """

    def __init__(self, pdu):
        self.pdu = pdu

        blocks = []
        blocks.append(self.pdu)
        self.data = b"".join(blocks)

    async def read(self, n=-1):
        if n == 0:
            return b""

        if n == -1:
            _to_read_data = self.data  # read all data
            _remaining_data = b""
        else:
            _to_read_data = self.data[:n]
            _remaining_data = self.data[n:]

        self.data = _remaining_data
        return _to_read_data

    async def readexactly(self, n):
        _to_read_data = self.data[:n]
        _remaining_data = self.data[n:]

        if len(_to_read_data) != n:
            # unable to read exactly n bytes
            raise asyncio.IncompleteReadError(partial=_to_read_data, expected=n)

        self.data = _remaining_data
        return _to_read_data

import os
import sys
import asyncio
import logging
from unittest import TestCase

import mock

from . import cli

logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.DEBUG)


class MockArgumentParser:
    def add_argument(self, *args, **kwargs):
        pass
    def parse_args(self, args=None, namespace=None):
        import argparse
        firee = open("examples/example_config.json", "r", encoding="utf-8")
        return argparse.Namespace( config=firee, dry_run=False, loglevel="DEBUG" )


def AsyncMock(*args, **kwargs):
    """
    see: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    """
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class TestCli(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v cli.test_cli.TestCli.test_bad_args
    """

    def setUp(self):
        self.parser = cli.make_parser()

    def tearDown(self):
        pass

    def _run(self, coro):
        """
        helper function that runs any coroutine in an event loop and passes its return value back to the caller.
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
        """
        return self.loop.run_until_complete(coro)

    def test_bad_args(self):
        with self.assertRaises(SystemExit) as raised_exception:
            args = self.parser.parse_args(["naz-cli", "-someBad", "-arguments"])

    def test_something(self):
        with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
            mock_ArgumentParser.return_value = MockArgumentParser()
            cli.main()
        # args = cli.make_parser_args(["--config", "examples/example_config.json"])

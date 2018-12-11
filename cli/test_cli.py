import sys
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
        return argparse.Namespace(config=firee, dry_run=False, loglevel="DEBUG")


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

    def test_bad_args(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["naz-cli", "-someBad", "-arguments"])

    def test_something(self):
        with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
            mock_ArgumentParser.return_value = MockArgumentParser()
            cli.main()

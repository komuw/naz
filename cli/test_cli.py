import io
import os
import sys
import copy
import json
import logging
import argparse
from unittest import TestCase

import mock
import docker
from . import cli

logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.DEBUG)


class MockArgumentParser:
    def __init__(self, naz_config):
        self.naz_config = naz_config

    def add_argument(self, *args, **kwargs):
        pass

    def parse_args(self, args=None, namespace=None):
        naz_config_file = io.StringIO(json.dumps(self.naz_config))
        return argparse.Namespace(config=naz_config_file, dry_run=True, loglevel="DEBUG")


class TestCli(TestCase):
    """
    run tests as:
        python -m unittest discover -v -s .
    run one testcase as:
        python -m unittest -v cli.test_cli.TestCli.test_bad_args
    """

    def setUp(self):
        self.parser = cli.make_parser()

        self.docker_client = docker.from_env()
        smppSimulatorName = "nazTestSmppSimulator"
        running_containers = self.docker_client.containers.list()
        for container in running_containers:
            container.stop()

        self.smpp_simulator = self.docker_client.containers.run(
            "komuw/smpp_server:v0.2",
            name=smppSimulatorName,
            detach=True,
            auto_remove=True,
            labels={"name": "smpp_server", "use": "running_naz_tets"},
            ports={"2775/tcp": 2775, "8884/tcp": 8884},
            stdout=True,
            stderr=True,
        )

        self.naz_config = {
            "smsc_host": "127.0.0.1",
            "smsc_port": 2775,
            "system_id": "smppclient1",
            "password": "password",
            "outboundqueue": "examples.example_klasses.ExampleRedisQueueInstance",
            "encoding": "gsm0338",
            "sequence_generator": "examples.example_klasses.ExampleSeqGen",
            "loglevel": "INFO",
            "log_metadata": {"environment": "production", "release": "canary"},
            "codec_errors_level": "ignore",
            "enquire_link_interval": 30,
            "rateLimiter": "examples.example_klasses.ExampleRateLimiter",
        }

    def tearDown(self):
        if os.environ.get("CI_ENVIRONMENT"):
            print("\n\nrunning in CI env.\n")
            self.smpp_simulator.remove(force=True)
        else:
            pass

    def test_bad_args(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["naz-cli", "-someBad", "-arguments"])

    def test_cli_success(self):
        with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
            mock_ArgumentParser.return_value = MockArgumentParser(naz_config=self.naz_config)
            cli.main()

    def test_cli_failure(self):
        with self.assertRaises(SystemExit):
            bad_config = copy.deepcopy(self.naz_config)
            bad_config.pop("outboundqueue")
            with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
                mock_ArgumentParser.return_value = MockArgumentParser(naz_config=bad_config)
                cli.main()

    def test_load_class_error(self):
        with self.assertRaises(SystemExit):
            bad_config = copy.deepcopy(self.naz_config)
            bad_config.update({"outboundqueue": "BareClass"})
            with mock.patch("argparse.ArgumentParser") as mock_ArgumentParser:
                mock_ArgumentParser.return_value = MockArgumentParser(naz_config=bad_config)
                cli.main()

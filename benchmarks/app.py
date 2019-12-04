import os

import naz

from .my_hook import BenchmarksHook
from .redis_broker import MyRedisBroker
from .my_logger import BenchmarksLogger

# run as:
#   naz-cli --client benchmarks.app.my_naz_client

country_code = "254"

my_naz_client = naz.Client(
    smsc_host=os.environ["SMSC_HOST"],
    smsc_port=2775,
    system_id="smppclient1",
    password=os.environ["SMSC_PASSWORD"],
    broker=MyRedisBroker(),
    hook=BenchmarksHook(),
    logger=BenchmarksLogger(
        logger_name="naz.benchmarks", level="DEBUG", log_metadata={"project": "naz_benchmarks"},
    ),
    socket_timeout=15.00,
    enquire_link_interval=80.00,
    address_range="^{0}".format(
        country_code
    ),  # any msisdns beginning with 254. See Appendix A of smpp spec
)

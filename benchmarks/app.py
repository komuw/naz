import os
import naz

from my_hook import BenchmarksHook
from redis_queue import MyRedisQueue

# run as:
#   naz-cli --client benchmarks.app.my_naz_client

my_naz_client = naz.Client(
    smsc_host="smsc_server",
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
    loglevel="DEBUG",
    log_metadata={"project": "naz_benchmarks"},
    outboundqueue=MyRedisQueue(),
    hook=BenchmarksHook(),
    connect_timeout=5.00,
)

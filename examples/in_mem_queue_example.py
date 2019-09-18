import os
import asyncio

import naz

loop = asyncio.get_event_loop()
outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000)
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
    outboundqueue=outboundqueue,
)

# queue messages to send
for i in range(0, 4):
    print("submit_sm round:", i)
    item_to_enqueue = {
        "version": "1",
        "smpp_command": naz.SmppCommand.SUBMIT_SM,
        "short_message": "Hello World-{0}".format(str(i)),
        "log_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))

    # altenatively::
    # loop.run_until_complete(
    #     cli.submit_sm(
    #         short_message="Hello World-{0}".format(str(i)),
    #         log_id="myid12345",
    #         source_addr="254722111111",
    #         destination_addr="254722999999",
    #     )
    # )

try:
    # 1. connect to the SMSC host
    # 2. bind to the SMSC host
    # 3. send any queued messages to SMSC
    # 4. read any data from SMSC
    # 5. continually check the state of the SMSC
    tasks = asyncio.gather(
        cli.connect(),
        cli.tranceiver_bind(),
        cli.dequeue_messages(),
        cli.receive_data(),
        cli.enquire_link(),
    )
    loop.run_until_complete(tasks)
except Exception as e:
    print("\n\t error occured. error={0}".format(str(e)))
finally:
    loop.run_until_complete(cli.unbind())
    loop.stop()

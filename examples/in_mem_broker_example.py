import os
import asyncio

import naz

loop = asyncio.get_event_loop()
broker = naz.broker.SimpleBroker(maxsize=1000)
cli = naz.Client(
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password=os.getenv("password", "password"),
    broker=broker,
)

# queue messages to send
for i in range(0, 4):
    print("submit_sm round:", i)
    loop.run_until_complete(
        broker.enqueue(
            naz.protocol.SubmitSM(
                short_message="Hello World-{0}".format(str(i)),
                log_id="myid1234-{0}".format(str(i)),
                source_addr="254722111111",
                destination_addr="254722999999",
            )
        )
    )

    # altenatively::
    # msg = naz.protocol.SubmitSM(
    #             short_message="Hello World-{0}".format(str(i)),
    #             log_id="myid12345",
    #             source_addr="254722111111",
    #             destination_addr="254722999999",
    #         )
    # loop.run_until_complete(
    #     cli.send_message(msg)
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

import asyncio

import naz


loop = asyncio.get_event_loop()
outboundqueue = naz.q.DefaultOutboundQueue(maxsize=1000, loop=loop)
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)

# queue messages to send
for i in range(0, 4):
    print("submit_sm round:", i)
    item_to_enqueue = {
        "event": "submit_sm",
        "short_message": "Hello World-{0}".format(str(i)),
        "correlation_id": "myid12345",
        "source_addr": "254722111111",
        "destination_addr": "254722999999",
    }
    loop.run_until_complete(outboundqueue.enqueue(item_to_enqueue))

    # altenatively::
    # loop.run_until_complete(
    #     cli.submit_sm(
    #         short_message="Hello World-{0}".format(str(i)),
    #         correlation_id="myid12345",
    #         source_addr="254722111111",
    #         destination_addr="254722999999",
    #     )
    # )

# connect to the SMSC host
reader, writer = loop.run_until_complete(cli.connect())
# bind to SMSC as a tranceiver
loop.run_until_complete(cli.tranceiver_bind())

try:
    # read any data from SMSC, send any queued messages to SMSC and continually check the state of the SMSC
    gathering = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(gathering)
    loop.run_forever()
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
    pass
finally:
    loop.run_until_complete(cli.unbind())
    loop.close()

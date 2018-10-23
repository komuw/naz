import naz, asyncio

loop = asyncio.get_event_loop()
outboundqueue = naz.q.SimpleOutboundQueue(maxsize=1000, loop=loop)
cli = naz.Client(
    async_loop=loop,
    smsc_host="127.0.0.1",
    smsc_port=2775,
    system_id="smppclient1",
    password="password",
    outboundqueue=outboundqueue,
)

# 1. network connect and bind
reader, writer = loop.run_until_complete(cli.connect())
loop.run_until_complete(cli.tranceiver_bind())
try:
    # 2. send SMS, read responses from SMSC, send status checks
    tasks = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
    loop.run_until_complete(tasks)
except Exception as e:
    print("exception occured. error={0}".format(str(e)))
finally:
    # 3. unbind
    loop.run_until_complete(cli.unbind())
    loop.close()

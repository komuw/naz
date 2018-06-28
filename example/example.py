import asyncio

import naz


rLimiter = naz.ratelimiter.RateLimiter(SEND_RATE=1, MAX_TOKENS=2, DELAY_FOR_TOKENS=8)
loop = asyncio.get_event_loop()
cli = naz.Client(
    async_loop=loop,
    SMSC_HOST="127.0.0.1",
    SMSC_PORT=2775,
    system_id="smppclient1",
    password="password",
    rateLimiter=rLimiter,
)

for i in range(0, 4):
    print("submit_sm round:", i)
    loop.run_until_complete(
        cli.submit_sm(
            msg="Hello World-{0}".format(str(i)),
            correlation_id="myid12345",
            source_addr="254722111111",
            destination_addr="254722999999",
        )
    )

reader, writer = loop.run_until_complete(cli.connect())
loop.run_until_complete(cli.tranceiver_bind())

gathering = asyncio.gather(cli.send_forever(), cli.receive_data(), cli.enquire_link())
loop.run_until_complete(gathering)

loop.run_forever()
loop.close()

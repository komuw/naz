import asyncio


async def say_boo():
    i = 0
    while True:
        print("...boo {0}".format(i))
        i += 1
        await asyncio.sleep(0.1)


async def say_baa():
    i = 0
    while True:
        await asyncio.sleep(0.1)
        print("...baa {0}".format(i))
        i += 1


# boo_task = asyncio.async(say_boo())
# baa_task = asyncio.async(say_baa())

loop = asyncio.get_event_loop()

gathering = asyncio.gather(say_boo(), say_baa())
loop.run_until_complete(gathering)


loop.run_forever()

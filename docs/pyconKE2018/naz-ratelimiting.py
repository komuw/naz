import naz
limiter = naz.ratelimiter.SimpleRateLimiter(
    send_rate=1, max_tokens=1, delay_for_tokens=6
)
cli = naz.Client(
    ...
    rateLimiter=limiter,
)


import naz
class AwesomeLimiter(naz.ratelimiter.BaseRateLimiter):
    async def limit(self):
        sleeper = 13.13
        print("\n\t rate limiting. sleep={}".format(sleeper))
        await asyncio.sleep(sleeper)

lim = AwesomeLimiter()
cli = naz.Client(
    ...
    rateLimiter=lim,
)

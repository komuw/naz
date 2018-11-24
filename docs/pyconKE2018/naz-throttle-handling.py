import naz

TH = naz.throttle.SimpleThrottleHandler(sampling_period=180,
                                        sample_size=45,
                                        deny_request_at=1.2)
cli = naz.Client(
    ...
    throttle_handler=TH,
)
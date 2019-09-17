import signal
import asyncio
import logging
import functools

import naz


async def _signal_handling(logger: naz.log.BaseLogger, client: naz.Client) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    try:
        for _signal in [signal.SIGHUP, signal.SIGQUIT, signal.SIGTERM]:
            loop.add_signal_handler(
                _signal,
                functools.partial(
                    asyncio.ensure_future,
                    _handle_termination_signal(logger=logger, _signal=_signal, client=client),
                ),
            )
    except ValueError as e:
        logger.log(
            logging.DEBUG,
            {
                "event": "naz.cli.signals",
                "stage": "end",
                "state": "this OS does not support the said signal",
                "error": str(e),
            },
        )


async def _handle_termination_signal(
    logger: naz.log.BaseLogger, _signal: "signal.Signals", client: naz.Client
) -> None:
    logger.log(
        logging.INFO,
        {
            "event": "naz.cli.signals",
            "stage": "start",
            "state": "received termination signal",
            "signal": _signal.name,
        },
    )

    await client.shutdown()

    logger.log(
        logging.INFO,
        {"event": "naz.cli.signals", "stage": "end", "state": "client has succesfully shutdown"},
    )
    return

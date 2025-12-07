import logging
from aiogram import Dispatcher


logger = logging.getLogger(__name__)


def register_error_handlers(dp: Dispatcher) -> None:
    dp.errors.register(on_error)


async def on_error(event):
    """
    Aiogram v3 error handler receives a single ErrorEvent that contains .update and .exception.
    Accept a single positional arg to avoid TypeError when dispatcher passes only one value.
    """
    exc = getattr(event, "exception", None)
    upd = getattr(event, "update", None)
    if exc:
        logger.exception("Unhandled error: %s | update=%s", exc, upd)
    else:
        logger.exception("Unhandled error event: %s", event)

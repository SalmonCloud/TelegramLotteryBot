import logging
from aiogram import BaseMiddleware
from aiogram.types import Message


class LogCommandMiddleware(BaseMiddleware):
    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)

    async def __call__(self, handler, event: Message, data):
        if self.enabled and getattr(event, "text", "") and event.text.startswith("/"):
            self.logger.info("Command received chat_id=%s user_id=%s text=%s", event.chat.id, event.from_user.id, event.text)
        return await handler(event, data)

import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message

from app.texts import zh_cn


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, delay_seconds: float = 1.0):
        super().__init__()
        self.delay_seconds = delay_seconds
        self._locks = {}

    async def __call__(self, handler, event: Message, data):
        key = (event.from_user.id, event.text or "")
        lock = self._locks.get(key)
        if lock and lock.locked():
            await event.answer(zh_cn.TEXT_TOO_FREQUENT)
            return

        lock = asyncio.Lock()
        self._locks[key] = lock
        async with lock:
            result = await handler(event, data)
            await asyncio.sleep(self.delay_seconds)
            return result

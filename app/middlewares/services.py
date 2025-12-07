from typing import Any, Dict

from aiogram import BaseMiddleware


class ServiceMiddleware(BaseMiddleware):
    def __init__(self, services: Dict[str, Any]):
        super().__init__()
        self.services = services

    async def __call__(self, handler, event, data):
        data.update(self.services)
        return await handler(event, data)

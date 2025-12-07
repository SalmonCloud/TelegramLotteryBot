from aiogram import BaseMiddleware
from aiogram.types import Message

from app.utils.permissions import is_chat_admin
from app.texts import zh_cn


class AdminACLMiddleware(BaseMiddleware):
    def __init__(self, target_chat_id: int):
        super().__init__()
        self.target_chat_id = target_chat_id

    async def __call__(self, handler, event: Message, data):
        if event.chat.id != self.target_chat_id:
            return
        if not await is_chat_admin(event.bot, event.chat.id, event.from_user.id):
            await event.answer(zh_cn.TEXT_NOT_ADMIN)
            return
        return await handler(event, data)

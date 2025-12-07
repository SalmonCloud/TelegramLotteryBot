from aiogram import Dispatcher, F
from aiogram.types import Message

from app.config import Config
from app.services.checkin_service import CheckinService
from app.utils.aiogram_helpers import is_command_message


def register_user_message_handlers(dp: Dispatcher, config: Config) -> None:
    # Only handle non-bot, non-command group messages to avoid blocking commands
    dp.message.register(
        on_group_message,
        ~F.from_user.is_bot,
        ~F.text.startswith("/"),
        F.chat.id == config.target_chat_id,
    )


async def on_group_message(message: Message, checkin_service: CheckinService):
    if is_command_message(message):
        return
    await checkin_service.process_message_for_checkin(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        message_id=message.message_id,
        message_time=message.date,
    )

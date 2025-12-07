from aiogram.types import Message


def is_command_message(message: Message) -> bool:
    return bool(message.text and message.text.startswith("/"))

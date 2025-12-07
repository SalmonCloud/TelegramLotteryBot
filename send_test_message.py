"""
Quick helper to send a test message to TARGET_CHAT_ID using current BOT_TOKEN.
Usage:
    python send_test_message.py "your message"
Falls back to a default text if no argument is provided.
"""

import asyncio
import os
import sys

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("TARGET_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("BOT_TOKEN or TARGET_CHAT_ID not set in environment/.env")

    text = "Test message from send_test_message.py"
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.send_message(chat_id=int(chat_id), text=text)
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

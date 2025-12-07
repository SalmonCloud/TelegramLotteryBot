from typing import Tuple, Optional

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tzlocal import get_localzone

from app.config import Config


def create_bot_and_dp(config: Config) -> Tuple[Bot, Dispatcher, Optional[AsyncIOScheduler]]:
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    scheduler: Optional[AsyncIOScheduler] = None
    if config.scheduler.enabled:
        scheduler = AsyncIOScheduler(timezone=config.scheduler.timezone or str(get_localzone()))

    return bot, dp, scheduler

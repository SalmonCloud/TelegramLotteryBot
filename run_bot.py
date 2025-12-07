import asyncio
import logging
from typing import Optional

from aiogram import Dispatcher
from aiogram import Bot
from dotenv import load_dotenv

from app.config import load_config, Config
from app.logging_config import setup_logging
from app.bot_loader import create_bot_and_dp
from app.handlers import register_handlers
from app.scheduler.jobs import register_jobs
from app.db.connection import init_db_pool, close_db_pool
from app.db.repositories import (
    CheckinRepository,
    SettingsRepository,
    PrizeRepository,
    LotteryRepository,
    AdminActionRepository,
)
from app.services.checkin_service import CheckinService
from app.services.settings_service import SettingsService
from app.services.prize_service import PrizeService
from app.services.lottery_service import LotteryService
from app.services.announce_service import AnnounceService
from app.services.stats_service import StatsService
from app.middlewares.services import ServiceMiddleware
from app.utils.commands import set_bot_commands
from app.middlewares.log_commands import LogCommandMiddleware
from app.utils import time_utils


async def _startup(config: Config) -> tuple[Bot, Dispatcher, SettingsService, PrizeService]:
    setup_logging()
    logging.getLogger("aiogram").setLevel(logging.DEBUG)
    logging.info("Loading bot with TARGET_CHAT_ID=%s", config.target_chat_id)

    await init_db_pool(config.db)
    bot, dp, scheduler = create_bot_and_dp(config)

    # Instantiate repositories and services (placeholder implementations)
    checkin_repo = CheckinRepository()
    settings_repo = SettingsRepository()
    prize_repo = PrizeRepository()
    lottery_repo = LotteryRepository()
    admin_repo = AdminActionRepository()

    checkin_service = CheckinService(checkin_repo)
    settings_service = SettingsService(settings_repo, timezone=config.scheduler.timezone)
    prize_service = PrizeService(prize_repo)
    lottery_service = LotteryService(lottery_repo, prize_repo, checkin_repo, settings_repo)
    announce_service = AnnounceService(bot)
    stats_service = StatsService(checkin_repo)

    # Log incoming commands with chat/user IDs (temporary helper)
    dp.message.middleware(LogCommandMiddleware(enabled=True))

    dp.message.middleware(
        ServiceMiddleware(
            {
                "checkin_service": checkin_service,
                "settings_service": settings_service,
                "prize_service": prize_service,
                "lottery_service": lottery_service,
                "announce_service": announce_service,
                "stats_service": stats_service,
                "admin_repo": admin_repo,
                "checkin_repo": checkin_repo,
            }
        )
    )

    register_handlers(dp, config)

    if scheduler:
        register_jobs(
            scheduler,
            bot,
            config,
            checkin_service=checkin_service,
            lottery_service=lottery_service,
            announce_service=announce_service,
            settings_service=settings_service,
        )
        scheduler.start()
        logging.info("Scheduler started")

    return bot, dp, settings_service, prize_service


async def main() -> None:
    load_dotenv()
    config = load_config()
    bot: Optional[Bot] = None
    dp: Optional[Dispatcher] = None
    settings_service: Optional[SettingsService] = None
    prize_service: Optional[PrizeService] = None

    try:
        bot, dp, settings_service, prize_service = await _startup(config)
        settings = await settings_service.get_settings(config.target_chat_id)
        await set_bot_commands(
            bot,
            config.target_chat_id,
            weekly_enabled=bool(settings.get("weekly_enabled", 0)),
        )
        # Startup check: 确保本周奖池已配置，否则提醒管理员
        if prize_service:
            today = time_utils.get_today_beijing()
            week_start, week_end = time_utils.get_week_start_end(today)
            prize_set = await prize_service.get_prize_set_for_week(config.target_chat_id, week_start, week_end)
            if not prize_set:
                warn_text = (
                    "⚠️ 本周周奖池未设置。\n"
                    f"请管理员尽快为 {week_start} ~ {week_end} 配置奖品集，避免抽奖时无奖池可用。"
                )
                await bot.send_message(chat_id=config.target_chat_id, text=warn_text)
        await dp.start_polling(bot)
    finally:
        await close_db_pool()
        logging.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

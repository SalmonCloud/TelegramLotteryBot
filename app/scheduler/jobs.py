from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from app.services.checkin_service import CheckinService
from app.services.lottery_service import LotteryService
from app.services.announce_service import AnnounceService
from app.services.settings_service import SettingsService
from app.utils import time_utils
from app.config import Config


def register_jobs(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    config: Config,
    *,
    checkin_service: CheckinService,
    lottery_service: LotteryService,
    announce_service: AnnounceService,
    settings_service: SettingsService,
) -> None:
    chat_id = config.target_chat_id

    # daily stats at 00:00 Beijing
    scheduler.add_job(
        job_daily_stats,
        "cron",
        hour="00",
        minute="00",
        kwargs={
            "chat_id": chat_id,
            "bot": bot,
            "checkin_service": checkin_service,
            "announce_service": announce_service,
        },
        id="daily_stats",
        replace_existing=True,
    )

    # weekly lottery Monday 00:00 Beijing
    scheduler.add_job(
        job_weekly_lottery,
        "cron",
        day_of_week="mon",
        hour=config.scheduler.weekly_draw_at.split(":")[0],
        minute=config.scheduler.weekly_draw_at.split(":")[1],
        kwargs={
            "chat_id": chat_id,
            "bot": bot,
            "lottery_service": lottery_service,
            "announce_service": announce_service,
            "settings_service": settings_service,
        },
        id="weekly_lottery",
        replace_existing=True,
    )


async def job_daily_stats(chat_id: int, bot: Bot, checkin_service: CheckinService, announce_service: AnnounceService):
    yesterday = time_utils.get_yesterday_beijing(datetime.utcnow())
    count = await checkin_service.count_yesterday_checkins(chat_id, datetime.utcnow())
    await announce_service.send_daily_stats(chat_id, yesterday, count)


async def job_weekly_lottery(
    chat_id: int,
    bot: Bot,
    lottery_service: LotteryService,
    announce_service: AnnounceService,
    settings_service: SettingsService,
):
    if not await settings_service.is_weekly_enabled(chat_id):
        return
    result = await lottery_service.run_weekly_lottery(chat_id, datetime.utcnow())
    await announce_service.send_weekly_lottery_result(chat_id, result)

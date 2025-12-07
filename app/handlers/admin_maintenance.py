from datetime import datetime, timedelta
import logging

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Config
from app.db.repositories import CheckinRepository, AdminActionRepository
from app.services.stats_service import StatsService
from app.texts import zh_cn
from app.utils.permissions import is_chat_admin
from app.utils import time_utils

logger = logging.getLogger(__name__)

ADMIN_MAINT_PREFIXES = (
    "/cleanup_checkins",
    "/stats_today",
    "/stats_week",
    "/admin_ping",
)


def register_admin_maintenance_handlers(dp: Dispatcher, config: Config) -> None:
    dp.message.register(cmd_cleanup_checkins, Command("cleanup_checkins", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_stats_today, Command("stats_today", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_stats_week, Command("stats_week", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_admin_ping, Command("admin_ping", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_admin_maintenance_unknown, F.text.startswith(ADMIN_MAINT_PREFIXES), F.chat.id == config.target_chat_id)


async def _ensure_admin(message: Message) -> bool:
    if not await is_chat_admin(message.bot, message.chat.id, message.from_user.id):
        await message.answer(zh_cn.TEXT_NOT_ADMIN)
        return False
    return True


async def cmd_cleanup_checkins(message: Message, checkin_repo: CheckinRepository, admin_repo: AdminActionRepository):
    if not await _ensure_admin(message):
        return
    logger.info("cmd_cleanup_checkins invoked chat_id=%s user_id=%s text=%s", message.chat.id, message.from_user.id, message.text)
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("用法：/cleanup_checkins YYYY-MM-DD 之前的数据会被删除")
        return
    try:
        cutoff = datetime.strptime(parts[1], "%Y-%m-%d").date()
    except ValueError:
        await message.answer("日期格式错误，应为 YYYY-MM-DD")
        return
    deleted = await checkin_repo.delete_before(message.chat.id, cutoff)
    await admin_repo.log_action(message.chat.id, message.from_user.id, "cleanup_checkins", {"cutoff": parts[1], "deleted": deleted})
    await message.answer(f"已删除 {cutoff} 之前的打卡记录，共 {deleted} 条。")


async def cmd_stats_today(message: Message, stats_service: StatsService):
    if not await _ensure_admin(message):
        return
    today = time_utils.get_today_beijing(message.date)
    logger.info("cmd_stats_today chat_id=%s user_id=%s today=%s", message.chat.id, message.from_user.id, today)
    data = await stats_service.get_daily_stats(message.chat.id, today)
    await message.answer(f"今日（{data['date']}）共有 {data['user_count']} 人打卡。")


async def cmd_stats_week(message: Message, stats_service: StatsService):
    if not await _ensure_admin(message):
        return
    today = time_utils.get_today_beijing(message.date)
    start, end = time_utils.get_week_start_end(today)
    logger.info("cmd_stats_week chat_id=%s user_id=%s start=%s end=%s", message.chat.id, message.from_user.id, start, end)
    data = await stats_service.get_week_stats(message.chat.id, start, end)
    lines = [f"本周统计 {start} ~ {end}"]
    for d in data["days"]:
        lines.append(f"{d['date']}: {d['user_count']} 人")
    await message.answer("\n".join(lines))


async def cmd_admin_maintenance_unknown(message: Message):
    if not await _ensure_admin(message):
        return
    try:
        await message.answer(f"管理员命令已收到：{message.text}")
    except Exception as e:
        logger.exception("Failed to reply admin unknown: %s", e)


async def cmd_admin_ping(message: Message):
    if not await _ensure_admin(message):
        return
    try:
        await message.answer("admin pong")
    except Exception as e:
        logger.exception("Failed to reply admin ping: %s", e)

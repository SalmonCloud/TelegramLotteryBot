from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Config
from app.services.settings_service import SettingsService
from app.services.lottery_service import LotteryService
from app.services.announce_service import AnnounceService
from app.db.repositories import AdminActionRepository
from app.texts import zh_cn
from app.utils.commands import update_admin_bot_commands
from app.utils.permissions import is_chat_admin
import logging

logger = logging.getLogger(__name__)


def register_admin_lottery_handlers(dp: Dispatcher, config: Config) -> None:
    dp.message.register(cmd_weekly_lottery_pause, Command("weekly_lottery_pause", ignore_mention=False), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_weekly_lottery_resume, Command("weekly_lottery_resume", ignore_mention=False), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_draw_now_weekly, Command("draw_now_weekly", ignore_mention=False), F.chat.id == config.target_chat_id)


async def _ensure_admin(message: Message) -> bool:
    # Allow anonymous admin mode (sender_chat == current chat) to pass
    if getattr(message, "sender_chat", None) and message.sender_chat.id == message.chat.id:
        return True
    is_admin = await is_chat_admin(message.bot, message.chat.id, message.from_user.id)
    logger.info("Admin check chat_id=%s user_id=%s is_admin=%s", message.chat.id, message.from_user.id, is_admin)
    if not is_admin:
        await message.answer(zh_cn.TEXT_NOT_ADMIN)
        return False
    return True


async def cmd_weekly_lottery_pause(message: Message, settings_service: SettingsService, admin_repo: AdminActionRepository):
    if not await _ensure_admin(message):
        return
    await settings_service.set_weekly_enabled(message.chat.id, False)
    await admin_repo.log_action(message.chat.id, message.from_user.id, "weekly_lottery_pause", {})
    settings = await settings_service.get_settings(message.chat.id)
    await update_admin_bot_commands(
        message.bot,
        message.chat.id,
        weekly_enabled=bool(settings.get("weekly_enabled", 0)),
    )
    await message.answer(zh_cn.TEXT_WEEKLY_LOTTERY_PAUSED)


async def cmd_weekly_lottery_resume(message: Message, settings_service: SettingsService, admin_repo: AdminActionRepository):
    if not await _ensure_admin(message):
        return
    await settings_service.set_weekly_enabled(message.chat.id, True)
    await admin_repo.log_action(message.chat.id, message.from_user.id, "weekly_lottery_resume", {})
    settings = await settings_service.get_settings(message.chat.id)
    await update_admin_bot_commands(
        message.bot,
        message.chat.id,
        weekly_enabled=bool(settings.get("weekly_enabled", 0)),
    )
    await message.answer(zh_cn.TEXT_WEEKLY_LOTTERY_RESUMED)


async def cmd_draw_now_weekly(message: Message, lottery_service: LotteryService, announce_service: AnnounceService, settings_service: SettingsService):
    if not await _ensure_admin(message):
        return
    settings = await settings_service.get_settings(message.chat.id)
    if not settings.get("weekly_enabled"):
        await message.answer(zh_cn.TEXT_WEEKLY_LOTTERY_PAUSED)
        return
    result = await lottery_service.run_weekly_lottery(message.chat.id, message.date)
    if result.round_id and result.total_participants == 0 and not result.winners:
        await message.answer("暂时没有有效参与者，未开奖。")
        return
    await announce_service.send_weekly_lottery_result(message.chat.id, result)

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Config
from app.services.prize_service import PrizeService
from app.services.settings_service import SettingsService
from app.texts import zh_cn
from app.utils.permissions import is_chat_admin
import logging

logger = logging.getLogger(__name__)

ADMIN_PRIZE_PREFIXES = (
    "/show_weekly_prizes",
)


def register_admin_prize_handlers(dp: Dispatcher, config: Config) -> None:
    dp.message.register(
        cmd_show_weekly_prizes,
        Command("show_weekly_prizes", ignore_mention=False),
        F.chat.id == config.target_chat_id,
    )
    # fallback admin command handler for prize-related commands
    dp.message.register(
        cmd_admin_unknown,
        F.text.startswith(ADMIN_PRIZE_PREFIXES),
        F.chat.id == config.target_chat_id,
    )


async def _ensure_admin(message: Message) -> bool:
    is_admin = await is_chat_admin(message.bot, message.chat.id, message.from_user.id)
    logger.info("Admin check chat_id=%s user_id=%s is_admin=%s", message.chat.id, message.from_user.id, is_admin)
    if not is_admin:
        await message.answer(zh_cn.TEXT_NOT_ADMIN)
        return False
    return True


async def cmd_show_weekly_prizes(message: Message, prize_service: PrizeService, settings_service: SettingsService):
    if not await _ensure_admin(message):
        return
    settings = await settings_service.get_settings(message.chat.id)
    weekly_enabled = bool(settings.get("weekly_enabled", 0))
    prizes = await prize_service.get_current_prizes(message.chat.id, set_type="weekly")
    lines = [zh_cn.TEXT_WEEKLY_LOTTERY_STATUS.format(status="开启" if weekly_enabled else "暂停")]
    if not weekly_enabled:
        lines.append(zh_cn.TEXT_WEEKLY_LOTTERY_DISABLED)
        lines.append("（当前奖池仍保留，恢复后生效）")
    lines.append(zh_cn.render_prize_list("Weekly 奖池", prizes))
    await message.answer("\n".join(lines))


async def cmd_admin_unknown(message: Message):
    if not await _ensure_admin(message):
        return
    await message.answer(f"管理员命令已收到：{message.text}")

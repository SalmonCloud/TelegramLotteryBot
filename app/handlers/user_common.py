from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Config
from app.services.checkin_service import CheckinService
from app.services.prize_service import PrizeService
from app.services.settings_service import SettingsService
from app.services.lottery_service import LotteryService
from app.services.announce_service import AnnounceService
from app.texts import zh_cn

ADMIN_COMMAND_PREFIXES = (
    "/weekly_lottery_pause",
    "/weekly_lottery_resume",
    "/draw_now_weekly",
    "/cleanup_checkins",
    "/stats_today",
    "/stats_week",
    "/show_weekly_prizes",
    "/admin_ping",
)


def register_user_common_handlers(dp: Dispatcher, config: Config) -> None:
    dp.message.register(cmd_ping, Command("ping", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_check_checkin, Command("check_checkin", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_lottery_info, Command("lottery_info", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_last_weekly_lottery_result, Command("last_weekly_lottery_result", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_help, Command("help", ignore_mention=True), F.chat.id == config.target_chat_id)
    dp.message.register(cmd_start, Command("start", ignore_mention=True), F.chat.id == config.target_chat_id)


async def cmd_check_checkin(message: Message, checkin_service: CheckinService):
    status = await checkin_service.get_checkin_status_for_user(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        now=message.date,
    )
    if status.today_checked:
        text = zh_cn.TEXT_CHECKIN_SUCCESS.format(
            date=status.checkin_date,
            week_count=status.week_checkin_count,
        )
    else:
        text = zh_cn.TEXT_CHECKIN_NOT_FOUND.format(
            date=status.checkin_date,
            week_count=status.week_checkin_count,
        )
    await message.answer(text)


async def cmd_lottery_info(message: Message, settings_service: SettingsService, prize_service: PrizeService):
    settings = await settings_service.get_settings(chat_id=message.chat.id)
    weekly_enabled = bool(settings.get("weekly_enabled"))
    if not weekly_enabled:
        await message.answer(zh_cn.TEXT_WEEKLY_LOTTERY_DISABLED)
        return

    weekly_prizes = await prize_service.get_current_prizes(message.chat.id, "weekly")
    prize_lines = zh_cn.render_prize_list("", weekly_prizes)
    prize_total = sum(int(p.get("quantity", 1)) for p in weekly_prizes) if weekly_prizes else 0
    full_factor = int(settings.get("full_attendance_factor", 2) or 2)
    weight_note = f"🎯 权重：当周打卡天数（满勤 7 天权重 ×{full_factor}）"
    text = zh_cn.TEXT_LOTTERY_INFO.format(
        status="进行中" if weekly_enabled else "暂停",
        weekly_draw_at=settings.get("weekly_draw_at"),
        prize_lines=prize_lines if prize_lines.strip() else "暂无奖品",
        prize_total=prize_total,
        weight_note=weight_note,
    )
    await message.answer(text)


async def cmd_last_weekly_lottery_result(message: Message, lottery_service: LotteryService, announce_service: AnnounceService):
    result = await lottery_service.get_last_weekly_result(message.chat.id, message.date)
    if not result:
        await message.answer(zh_cn.TEXT_LAST_WEEKLY_RESULT_NOT_FOUND)
        return
    await announce_service.send_weekly_lottery_result(message.chat.id, result)


def _help_text() -> str:
    return (
        "👋 欢迎使用本群打卡抽奖机器人！\n"
        "------\n"
        "可用命令（用户侧）\n"
        "• /check_checkin - 查看今日是否已打卡\n"
        "• /lottery_info - 查看本周奖池与规则\n"
        "• /last_weekly_lottery_result - 查看上一期周抽奖结果\n"
        "------\n"
        "抽奖规则概要\n"
        "• 在群内至少发送一条任意非命令消息即完成当日打卡\n"
        "• 打卡越多权重越高，满勤 7 天权重×{full_factor}\n"
        "• 每周抽奖时间：{weekly_draw_at}（北京时间）\n"
        "• 管理员可随时暂停/恢复周抽奖\n"
    )


async def cmd_help(message: Message, settings_service: SettingsService):
    settings = await settings_service.get_settings(chat_id=message.chat.id)
    full_factor = int(settings.get("full_attendance_factor", 2) or 2)
    weekly_draw_at = settings.get("weekly_draw_at", "00:00")
    text = _help_text().format(full_factor=full_factor, weekly_draw_at=weekly_draw_at)
    await message.answer(text)


async def cmd_start(message: Message, settings_service: SettingsService):
    await cmd_help(message, settings_service)


async def cmd_ping(message: Message):
    try:
        await message.answer("pong")
    except Exception as e:
        import logging

        logging.exception("Failed to reply ping: %s", e)

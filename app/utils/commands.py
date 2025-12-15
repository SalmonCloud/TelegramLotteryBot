import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChatAdministrators
from aiogram.exceptions import TelegramBadRequest


def _build_admin_commands(weekly_enabled: bool):
    commands = [
        BotCommand(command="weekly_lottery_pause", description="【管理员】暂停周抽奖"),
        BotCommand(command="weekly_lottery_resume", description="【管理员】恢复周抽奖"),
        BotCommand(command="cleanup_checkins", description="【管理员】清理打卡"),
        BotCommand(command="stats_today", description="【管理员】今日统计"),
        BotCommand(command="stats_week", description="【管理员】本周统计"),
        BotCommand(command="help", description="查看指令与抽奖规则"),
    ]
    if weekly_enabled:
        commands.append(BotCommand(command="draw_now_weekly", description="【管理员】立即周抽"))
        commands.append(BotCommand(command="show_weekly_prizes", description="【管理员】查看周奖池"))
    return commands


async def update_admin_bot_commands(bot: Bot, target_chat_id: int, *, weekly_enabled: bool) -> None:
    commands = _build_admin_commands(weekly_enabled)
    try:
        await bot.set_my_commands(commands=commands, scope=BotCommandScopeChatAdministrators(chat_id=target_chat_id))
    except TelegramBadRequest as e:
        logging.warning("Failed to update admin commands for chat_id=%s: %s", target_chat_id, e.message)


async def set_bot_commands(bot: Bot, target_chat_id: int, *, weekly_enabled: bool = True) -> None:
    await bot.set_my_commands(
        commands=[
            BotCommand(command="checkin_status", description="查询今日/本周打卡"),
            BotCommand(command="lottery_info", description="抽奖规则与奖池"),
            BotCommand(command="last_weekly_lottery_result", description="查看上一期周抽奖结果"),
            BotCommand(command="help", description="查看指令与抽奖规则"),
        ],
        scope=BotCommandScopeDefault(),
    )

    await update_admin_bot_commands(
        bot,
        target_chat_id,
        weekly_enabled=weekly_enabled,
    )

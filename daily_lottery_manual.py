import os
import random
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telethon import TelegramClient

# 加载环境变量
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("AZIHAIMO_ID"))  # -100 开头的超级群 ID
EXCLUDE_IDS = set(int(x) for x in os.getenv("EXCLUDE_IDS", "").split(",") if x.strip())

tz = pytz.timezone("Asia/Shanghai")

# Telethon client（用用户账号登录）
client = TelegramClient("lottery_session", API_ID, API_HASH)

async def fetch_participants(date_str: str, n: int, min_msg: int):
    target_date = datetime.strptime(date_str, "%Y/%m/%d").date()
    start_bj = tz.localize(datetime.combine(target_date, datetime.min.time()))
    end_bj = tz.localize(datetime.combine(target_date, datetime.max.time()))

    start_utc = start_bj.astimezone(pytz.UTC)
    end_utc = end_bj.astimezone(pytz.UTC)

    user_counts = {}
    print("start_utc:", start_utc, "end_utc:", end_utc)
    async for msg in client.iter_messages(GROUP_ID, offset_date=start_utc, reverse=True):
        # print(f"date: {msg.date}; text: {msg.text}; action: {msg.action}")
        if msg.date > end_utc:
            break
        if start_utc <= msg.date <= end_utc:
            # 在区间内
            if msg.sender_id and msg.sender_id not in EXCLUDE_IDS:
                # 确认发送者是用户对象，并且不是 bot
                if msg.sender and getattr(msg.sender, "bot", False) is False:
                    user_counts[msg.sender_id] = user_counts.get(msg.sender_id, 0) + 1

    eligible = [
        uid for uid, count in user_counts.items()
        if count >= min_msg and uid not in EXCLUDE_IDS
    ]
    if not eligible:
        return None, user_counts

    if len(eligible) < n:
        n = len(eligible)

    winners = random.sample(eligible, n)
    winners_info = []
    for uid in winners:
        user = await client.get_entity(uid)
        winners_info.append(user)

    return winners_info, user_counts


async def lottery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """命令触发: /lottery 2025/09/27 3 2"""
    try:
        date_str = context.args[0]       # 日期
        n = int(context.args[1])         # 抽奖人数
        min_msg = int(context.args[2])   # 最少消息数
    except (IndexError, ValueError):
        await update.message.reply_text("用法: /lottery YYYY/MM/DD N minMessage")
        return

    async with client:
        winners, stats = await fetch_participants(date_str, n, min_msg)

    if not winners:
        await update.message.reply_text(f"{date_str} 没有人满足条件 (至少 {min_msg} 条消息)。")
    else:
        # 打印奖池名单
        pool_info = []
        async with client:
            for uid, count in stats.items():
                if count >= min_msg:
                    user = await client.get_entity(uid)
                    name = user.first_name or user.username or str(uid)
                    pool_info.append(f"{name} ({count}条消息)")

        pool_msg = f"📋 {date_str} 奖池名单 (至少 {min_msg} 条消息):\n" + "\n".join(f"- {p}" for p in pool_info)

        # 抽奖结果（可点击 @）
        result_lines = []
        for user in winners:
            name = user.first_name or user.username or str(user.id)
            mention = f"<a href='tg://user?id={user.id}'>{name}</a>"
            result_lines.append(f"- {mention}")

        result_msg = "🎉 抽奖结果：\n" + "\n".join(result_lines)

        final_msg = pool_msg + "\n\n" + result_msg

        print(final_msg)

        await update.message.reply_text(final_msg, parse_mode="HTML")


async def send_startup_message(app: Application):
    """Bot 启动时发提示"""
    help_text = (
        "🤖 抽奖机器人已启动！\n\n"
        "使用方法：\n"
        "/lottery YYYY/MM/DD N minMessage\n\n"
        "例如：\n"
        "/lottery 2025/09/27 3 2\n"
        "表示在 2025/09/27 当天，从发言不少于 2 条的成员中抽 3 人。"
    )
    await app.bot.send_message(chat_id=GROUP_ID, text=help_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_startup_message(context.application)


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(send_startup_message)  # 启动时执行
        .build()
    )

    app.add_handler(CommandHandler("lottery", lottery_command))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot 已启动，使用 /lottery YYYY/MM/DD N minMessage 触发抽奖")
    app.run_polling()


if __name__ == "__main__":
    main()

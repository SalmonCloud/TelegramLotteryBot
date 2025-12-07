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
GROUP_ID = int(os.getenv("SALMONCLOUD_GROUP_ID"))  # -100 开头的超级群 ID
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


async def fetch_group_members():
    """返回当前群组中可参与抽奖的成员列表（去除机器人与 EXCLUDE_IDS）"""
    members = []
    async with client:
        async for user in client.iter_participants(GROUP_ID):
            # 跳过机器人与排除名单
            if getattr(user, "bot", False):
                continue
            if user.id in EXCLUDE_IDS:
                continue
            members.append(user)
            print(f"{getattr(user, 'username', None)} : {getattr(user, "id", None)}")
    return members


def display_name(user):
    """生成一个可读名字（没有用户名时用姓名 / ID）"""
    name = getattr(user, "username", None)
    if name:
        return name
    else:
        return str(user.id)


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
        # 不再打印所有符合条件的用户名单，仅展示符合条件的人数
        eligible_count = sum(1 for _, count in stats.items() if count >= min_msg)
        pool_msg = (
            f"📋 {date_str} 当天满足发言条件的人数：{eligible_count}（至少 {min_msg} 条消息）"
        )

        # 抽奖结果（可点击 @）
        result_lines = []
        for user in winners:
            name = getattr(user, "username", None) or getattr(user, "title", None) or str(user.id)
            mention = f"<a href='tg://user?id={user.id}'>{name}</a>"
            result_lines.append(f"- {mention}")

        result_msg = "🎉 抽奖结果：\n" + "\n".join(result_lines)

        final_msg = pool_msg + "\n\n" + result_msg

        print(final_msg)

        await update.message.reply_text(final_msg, parse_mode="HTML")


# 抽群组里的所有人，除了 bot 和排除名单
async def lottery_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """命令触发: /lottery_all N   （N 为要抽的人数）"""
    try:
        n = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("用法: /lottery_all N\n示例：/lottery_all 3")
        return

    # 拉取可抽奖成员
    members = await fetch_group_members()
    total = len(members)
    if total == 0:
        await update.message.reply_text("当前群暂未获取到可参与抽奖的成员。")
        return

    if n > total:
        n = total  # 保护：请求人数大于奖池人数时，改为全员中奖
        await update.message.reply_text(f"群组成员数量不足奖品数，奖品改为 {n} 份\n\n")

    winners = random.sample(members, n)

    # 结果信息（可点 @ 的 mention）
    result_lines = []
    for user in winners:
        name = display_name(user)
        mention = f"<a href='tg://user?id={user.id}'>{name}</a>"
        result_lines.append(f"- {mention}")

    final_msg = (
        "🎉 全员抽奖（无需发言门槛）\n"
        f"参与人数（去除 bot 和 SalmonCloud 管理员）：{total}\n"
        f"中奖人数：{n}\n\n"
        "🏆 中奖结果：\n" + "\n".join(result_lines)
    )

    await update.message.reply_text(final_msg, parse_mode="HTML")



async def send_startup_message(app: Application):
    """Bot 启动时发提示"""
    help_text = (
        "🤖 抽奖机器人已启动！\n\n"
        "使用方法：\n"
        "/lottery YYYY/MM/DD N minMessage  —— 在某天发言≥minMessage 的成员中抽 N 人\n"
        "/lottery_all N                    —— 在当前群所有成员中直接抽 N 人\n\n"
        "示例：\n"
        "/lottery 2025/09/27 3 2\n"
        "/lottery_all 3"
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
    app.add_handler(CommandHandler("lottery_all", lottery_all_command))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot 已启动")
    app.run_polling()


if __name__ == "__main__":
    main()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler
import os
import random
from dotenv import load_dotenv
from datetime import datetime, time
import pytz

# 加载环境变量
load_dotenv()
# api_id = int(os.getenv('API_ID'))
# api_hash =  os.getenv("API_HASH")
BOT_TOKEN = os.getenv('BOT_TOKEN')
Group_username = "salmoncloud_official"  # 群组username
participants = set()    # 记录发言过的用户

# session_name 是本地保存登录信息的文件名，下次运行就不用再输入验证码了
# client = TelegramClient('test_session', api_id, api_hash)

# # 指定日期（北京时间）
# date_str = "2025/09/21"
# target_date = datetime.strptime(date_str, "%Y/%m/%d").date()
tz = pytz.timezone("Asia/Shanghai")  # 北京时间

async def record_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        participants.add(user.id)

async def run_lottery(context: ContextTypes.DEFAULT_TYPE):
    global participants
    if not participants:
        await context.bot.send_message(Group_username, "今天没有人发言，无法抽奖")
        return

    N = 3   # 每日抽奖人数
    if len(participants) < N:
        await context.bot.send_message(Group_username, f"今天发言人数不足 {N}人，奖品直接无法全量发出")
        N = len(participants)

    winners = random.sample(participants, N)
    winners_name = []
    for user_id in winners:
        member = await context.bot.get_chat_member(Group_username, user_id)
        name = member.user.full_name
        winners_name.append(name)

    lottery_msg = "🎉 今日抽奖结果：\n" + "\n".join(f"- {w}" for w in winners_name)
    await context.bot.send_message(lottery_msg)

    participants = set()


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("lottery", run_lottery))
    app.add_handler(MessageHandler(None, record_participants))

    # 定时任务（每天 23:59 抽奖）
    app.job_queue.run_daily(run_lottery, time(hour=23, minute=59, tzinfo=tz))

    app.run_polling()

if __name__ == "__main__":
    main()
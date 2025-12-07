from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder().token(BOT_TOKEN).build()

async def echo(update: Update, context):
    print("群组ID:", update.effective_chat.id)

app.add_handler(MessageHandler(filters.ALL, echo))
app.run_polling()

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# === 读取环境变量 ===
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("AZIHAIMO_ID"))  # 另一个群的 -100 开头的超级群 ID

# Telethon 客户端
client = TelegramClient("dump_session", API_ID, API_HASH)


async def dump_all_messages():
    count = 0
    async with client:
        async for msg in client.iter_messages(GROUP_ID, limit=100, reverse=False):  # reverse=True 从最早的往后抓
            print(f"{count}: id={msg.id}, date={msg.date}, sender_id={msg.sender_id}, text={msg.text!r}")
            count += 1

        print(f"\n📌 一共抓取到 {count} 条消息")
        if count > 0:
            print("✅ 最早的消息日期就是上面第一条的 date")


if __name__ == "__main__":
    asyncio.run(dump_all_messages())

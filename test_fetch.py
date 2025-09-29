import asyncio
from daily_lottery_manual import client, fetch_participants

async def main():
    async with client:
        winners, stats = await fetch_participants("2025/09/28", 3, 2)
        print("候选用户统计：", stats)
        print("抽奖结果：", winners)

if __name__ == "__main__":
    asyncio.run(main())

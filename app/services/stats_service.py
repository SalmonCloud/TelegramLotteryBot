from datetime import date, timedelta

from app.db.repositories import CheckinRepository


class StatsService:
    def __init__(self, repo: CheckinRepository):
        self.repo = repo

    async def get_daily_stats(self, chat_id: int, target_date: date) -> dict:
        count = await self.repo.count_yesterday_checkins(chat_id, target_date)
        return {"date": target_date, "user_count": count}

    async def get_week_stats(self, chat_id: int, week_start: date, week_end: date) -> dict:
        days = []
        current = week_start
        while current <= week_end:
            cnt = await self.repo.count_yesterday_checkins(chat_id, current)
            days.append({"date": current, "user_count": cnt})
            current += timedelta(days=1)
        return {"week_start": week_start, "week_end": week_end, "days": days}

from datetime import datetime, date

from app.db.repositories import CheckinRepository
from app.utils import time_utils
from app.models.dto import CheckinStatusDTO


class CheckinService:
    def __init__(self, repo: CheckinRepository):
        self.repo = repo

    async def process_message_for_checkin(self, chat_id: int, user_id: int, message_id: int, message_time: datetime) -> None:
        checkin_date = time_utils.get_today_beijing(message_time)
        await self.repo.mark_checkin(chat_id, user_id, checkin_date, message_id, message_time)

    async def get_checkin_status_for_user(self, chat_id: int, user_id: int, now: datetime) -> CheckinStatusDTO:
        today = time_utils.get_today_beijing(now)
        week_start, week_end = time_utils.get_week_start_end(today)
        today_row = await self.repo.get_today_checkin(chat_id, user_id, today)
        week_count = await self.repo.get_week_checkin_count(chat_id, user_id, week_start, week_end)
        return CheckinStatusDTO(today_checked=bool(today_row), week_checkin_count=week_count, checkin_date=today)

    async def count_yesterday_checkins(self, chat_id: int, now: datetime) -> int:
        yesterday = time_utils.get_yesterday_beijing(now)
        return await self.repo.count_yesterday_checkins(chat_id, yesterday)

    async def get_weekly_checkin_map(self, chat_id: int, week_start: date, week_end: date):
        return await self.repo.get_weekly_checkin_counts_for_all_users(chat_id, week_start, week_end)

    async def delete_before(self, chat_id: int, cutoff_date: date) -> int:
        return await self.repo.delete_before(chat_id, cutoff_date)

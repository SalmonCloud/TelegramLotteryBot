from typing import List, Dict, Optional
from datetime import date

from app.db.repositories import PrizeRepository
from app.utils import time_utils


class PrizeService:
    def __init__(self, repo: PrizeRepository):
        self.repo = repo

    async def get_current_prizes(self, chat_id: int, set_type: str) -> List[Dict]:
        today = time_utils.get_today_beijing()
        start, end = time_utils.get_week_start_end(today)
        cur = await self.repo.get_prize_set_for_period(chat_id, set_type, start, end)
        if not cur:
            return []
        items = await self.repo.list_prizes_for_set(cur["id"])
        return items

    async def get_prize_set_for_week(self, chat_id: int, week_start: date, week_end: date) -> Optional[Dict]:
        return await self.repo.get_prize_set_for_period(chat_id, "weekly", week_start, week_end)

    async def ensure_prize_set_for_week(self, chat_id: int, week_start: date, week_end: date, *, fallback_source_set_id: Optional[int] = None) -> Optional[int]:
        existing = await self.repo.get_prize_set_for_period(chat_id, "weekly", week_start, week_end)
        if existing:
            return existing["id"]
        source = None
        if fallback_source_set_id:
            source = {"id": fallback_source_set_id}
        else:
            source = await self.repo.get_latest_prize_set_before(chat_id, "weekly", week_start)
        if not source:
            return None
        source_items = await self.repo.list_prizes_for_set(source["id"])
        new_set_id = await self.repo.create_prize_set(chat_id, "weekly", week_start, week_end)
        for idx, p in enumerate(source_items, start=1):
            await self.repo.insert_prize_item(
                set_id=new_set_id,
                name=p["name"],
                description=p.get("description"),
                quantity=p.get("quantity", 1),
                enabled=p.get("enabled", True),
                prize_rank=p.get("prize_rank", idx),
            )
        return new_set_id

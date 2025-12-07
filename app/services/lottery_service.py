from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import random

from app.db.repositories import LotteryRepository, PrizeRepository, CheckinRepository, SettingsRepository
from app.models.dto import LotteryResultDTO, LotteryWinnerDTO
from app.utils import time_utils


class LotteryService:
    def __init__(self, lottery_repo: LotteryRepository, prize_repo: PrizeRepository, checkin_repo: CheckinRepository, settings_repo: SettingsRepository):
        self.lottery_repo = lottery_repo
        self.prize_repo = prize_repo
        self.checkin_repo = checkin_repo
        self.settings_repo = settings_repo

    async def run_weekly_lottery(self, chat_id: int, now: datetime) -> LotteryResultDTO:
        today = time_utils.get_today_beijing(now)
        last_week_target = today - timedelta(days=7)
        week_start, week_end = time_utils.get_week_start_end(last_week_target)

        existing = await self.lottery_repo.get_round_by_period(chat_id, "weekly", week_start, week_end)
        if existing and existing.get("status") == "done":
            winners_rows = await self.lottery_repo.get_winners(existing["id"])
            winners = [LotteryWinnerDTO(user_id=w["user_id"], prize_name=w["prize_name"], prize_description=w.get("prize_description") or "", prize_rank=w.get("prize_rank", 1)) for w in winners_rows]
            return LotteryResultDTO(
                round_id=existing["id"],
                round_type="weekly",
                period_start_date=week_start,
                period_end_date=week_end,
                total_participants=existing.get("total_participants", 0),
                total_tickets=existing.get("total_tickets", 0),
                winners=winners,
            )

        checkin_map = await self.checkin_repo.get_weekly_checkin_counts_for_all_users(chat_id, week_start, week_end)
        if not checkin_map:
            raise ValueError("No participants for weekly lottery")

        settings = await self.settings_repo.get_or_create_settings(chat_id, "Asia/Shanghai")
        full_factor = int(settings.get("full_attendance_factor", 2) or 2)

        entries = []
        total_weight = 0
        for user_id, days in checkin_map.items():
            is_full = days == 7
            weight = days * (full_factor if is_full else 1)
            entries.append({"chat_id": chat_id, "user_id": user_id, "checkin_days": days, "weight": weight, "is_full_attendance": is_full})
            total_weight += weight

        prize_set = await self.prize_repo.get_prize_set_for_period(chat_id, "weekly", week_start, week_end)
        if not prize_set:
            # try to clone from latest before this week
            latest = await self.prize_repo.get_latest_prize_set_before(chat_id, "weekly", week_start)
            if latest:
                new_set_id = await self.prize_repo.create_prize_set(chat_id, "weekly", week_start, week_end)
                source_items = await self.prize_repo.list_prizes_for_set(latest["id"])
                for idx, p in enumerate(source_items, start=1):
                    await self.prize_repo.insert_prize_item(
                        set_id=new_set_id,
                        name=p["name"],
                        description=p.get("description"),
                        quantity=p.get("quantity", 1),
                        enabled=p.get("enabled", True),
                        prize_rank=p.get("prize_rank", idx),
                    )
                prize_set = {"id": new_set_id}
            else:
                raise ValueError("No current weekly prize set")
        prize_items = await self.prize_repo.list_prizes_for_set(prize_set["id"])

        round_id = existing["id"] if existing else await self.lottery_repo.create_round(chat_id, "weekly", week_start, week_end, None, None, prize_set["id"])

        winners = self._draw_winners(entries, prize_items)

        await self.lottery_repo.add_entries(round_id, entries)
        await self.lottery_repo.add_winners(round_id, winners)
        await self.lottery_repo.complete_round(round_id, total_participants=len(entries), total_tickets=total_weight)

        winner_dtos = [
            LotteryWinnerDTO(
                user_id=w["user_id"],
                prize_name=w["prize_name"],
                prize_description=w.get("prize_description") or "",
                prize_rank=w.get("prize_rank", 1),
            )
            for w in winners
        ]

        # Prepare下一周奖池：若未配置则自动沿用本周奖池
        next_week_start = week_end + timedelta(days=1)
        next_week_end = next_week_start + timedelta(days=6)
        has_next = await self.prize_repo.get_prize_set_for_period(chat_id, "weekly", next_week_start, next_week_end)
        if not has_next and prize_set.get("id"):
            await self._clone_prize_set_for_period(chat_id, prize_set.get("id"), next_week_start, next_week_end)

        return LotteryResultDTO(
            round_id=round_id,
            round_type="weekly",
            period_start_date=week_start,
            period_end_date=week_end,
            total_participants=len(entries),
            total_tickets=total_weight,
            winners=winner_dtos,
        )

    async def _clone_prize_set_for_period(self, chat_id: int, source_set_id: int, period_start: date, period_end: date) -> Optional[int]:
        source_items = await self.prize_repo.list_prizes_for_set(source_set_id)
        new_set_id = await self.prize_repo.create_prize_set(chat_id, "weekly", period_start, period_end)
        for idx, p in enumerate(source_items, start=1):
            await self.prize_repo.insert_prize_item(
                set_id=new_set_id,
                name=p["name"],
                description=p.get("description"),
                quantity=p.get("quantity", 1),
                enabled=p.get("enabled", True),
                prize_rank=p.get("prize_rank", idx),
            )
        return new_set_id

    async def get_last_weekly_result(self, chat_id: int, now: datetime) -> LotteryResultDTO | None:
        today = time_utils.get_today_beijing(now)
        last_week_target = today - timedelta(days=7)
        week_start, week_end = time_utils.get_week_start_end(last_week_target)

        existing = await self.lottery_repo.get_round_by_period(chat_id, "weekly", week_start, week_end)
        if not existing or existing.get("status") != "done":
            return None

        winners_rows = await self.lottery_repo.get_winners(existing["id"])
        winners = [
            LotteryWinnerDTO(
                user_id=w["user_id"],
                prize_name=w["prize_name"],
                prize_description=w.get("prize_description") or "",
                prize_rank=w.get("prize_rank", 1),
            )
            for w in winners_rows
        ]

        return LotteryResultDTO(
            round_id=existing["id"],
            round_type="weekly",
            period_start_date=week_start,
            period_end_date=week_end,
            total_participants=existing.get("total_participants", 0),
            total_tickets=existing.get("total_tickets", 0),
            winners=winners,
        )

    async def run_custom_lottery(self, chat_id: int, start_date: date, end_date: date, round_type: str, note: str) -> LotteryResultDTO:
        raise NotImplementedError("Custom lottery not implemented yet")

    def _draw_winners(self, entries: List[Dict], prize_items: List[Dict]) -> List[Dict]:
        winners = []
        # Copy entries to mutable list
        mutable_entries = [{**e} for e in entries]
        no_participants_left = False
        for prize in prize_items:
            for _ in range(prize.get("quantity", 1)):
                # filter only positive weight users not already winners
                available = [e for e in mutable_entries if e["weight"] > 0 and e.get("user_id") not in [w["user_id"] for w in winners]]
                if not available:
                    no_participants_left = True
                    break
                total_weight = sum(e["weight"] for e in available)
                if total_weight <= 0:
                    break
                pick = random.randint(1, total_weight)
                cumulative = 0
                chosen = None
                for e in available:
                    cumulative += e["weight"]
                    if pick <= cumulative:
                        chosen = e
                        break
                if not chosen:
                    continue
                winners.append(
                    {
                        "chat_id": prize.get("chat_id") or entries[0]["chat_id"],
                        "user_id": chosen["user_id"],
                        "prize_set_id": prize.get("set_id") or prize.get("id") or None,
                        "prize_name": prize.get("name"),
                        "prize_description": prize.get("description"),
                        "prize_rank": prize.get("prize_rank", 1),
                    }
                )
            if no_participants_left:
                break
        return winners

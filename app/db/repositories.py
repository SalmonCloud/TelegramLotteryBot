"""
Repository layer built on top of queries.py.
"""

import json
from datetime import date, datetime
from typing import Dict, List, Optional

from app.db import queries


class CheckinRepository:
    async def mark_checkin(self, chat_id: int, user_id: int, checkin_date: date, message_id: int, message_time: datetime) -> None:
        await queries.insert_or_increment_daily_checkin(chat_id, user_id, checkin_date, message_id, message_time)

    async def get_today_checkin(self, chat_id: int, user_id: int, checkin_date: date) -> Optional[Dict]:
        return await queries.get_user_checkin_for_date(chat_id, user_id, checkin_date)

    async def get_week_checkin_count(self, chat_id: int, user_id: int, week_start: date, week_end: date) -> int:
        return await queries.count_user_checkins_between(chat_id, user_id, week_start, week_end)

    async def count_yesterday_checkins(self, chat_id: int, target_date: date) -> int:
        return await queries.count_distinct_users_for_date(chat_id, target_date)

    async def get_weekly_checkin_counts_for_all_users(self, chat_id: int, week_start: date, week_end: date) -> Dict[int, int]:
        return await queries.get_weekly_checkin_counts_for_all_users(chat_id, week_start, week_end)

    async def delete_before(self, chat_id: int, cutoff_date: date) -> int:
        return await queries.delete_checkins_before_date(chat_id, cutoff_date)

    async def get_user_ids_for_date(self, chat_id: int, checkin_date: date) -> List[int]:
        return await queries.get_user_ids_for_date(chat_id, checkin_date)


class SettingsRepository:
    async def get_or_create_settings(self, chat_id: int, timezone: str) -> Dict:
        row = await queries.get_lottery_settings(chat_id)
        if not row:
            await queries.insert_default_lottery_settings(chat_id, timezone)
            row = await queries.get_lottery_settings(chat_id)
        return row

    async def set_weekly_enabled(self, chat_id: int, enabled: bool) -> None:
        await queries.update_weekly_enabled(chat_id, enabled)

    async def set_draw_times(self, chat_id: int, weekly_time: str) -> None:
        await queries.update_draw_times(chat_id, weekly_time)

    async def set_full_attendance_factor(self, chat_id: int, factor: int) -> None:
        await queries.update_full_attendance_factor(chat_id, factor)

    async def get_settings(self, chat_id: int) -> Optional[Dict]:
        return await queries.get_lottery_settings(chat_id)


class PrizeRepository:
    async def get_prize_set_for_period(self, chat_id: int, set_type: str, period_start: date, period_end: date) -> Optional[Dict]:
        return await queries.get_prize_set_for_period(chat_id, set_type, period_start, period_end)

    async def get_latest_prize_set_before(self, chat_id: int, set_type: str, ref_date: date) -> Optional[Dict]:
        return await queries.get_latest_prize_set_before(chat_id, set_type, ref_date)

    async def list_prizes_for_set(self, set_id: int) -> List[Dict]:
        return await queries.get_prize_items_for_set(set_id)

    async def create_prize_set(self, chat_id: int, set_type: str, valid_from: date | None, valid_to: date | None) -> int:
        return await queries.insert_prize_set(chat_id, set_type, valid_from, valid_to)

    async def insert_prize_item(self, set_id: int, name: str, description: str | None, quantity: int, enabled: bool, prize_rank: int) -> None:
        await queries.insert_prize_item(set_id, name, description, quantity, enabled, prize_rank)

    async def update_prize_item_enabled(self, item_id: int, enabled: bool) -> None:
        await queries.update_prize_item_enabled(item_id, enabled)


class LotteryRepository:
    async def get_round_by_period(self, chat_id: int, round_type: str, period_start: date, period_end: date) -> Optional[Dict]:
        return await queries.get_round_by_period(chat_id, round_type, period_start, period_end)

    async def create_round(self, chat_id: int, round_type: str, period_start_date: date, period_end_date: date, note: str | None, prize_set_id: int | None) -> int:
        return await queries.create_lottery_round(chat_id, round_type, period_start_date, period_end_date, note, prize_set_id)

    async def complete_round(self, round_id: int, total_participants: int, total_tickets: int) -> None:
        await queries.mark_lottery_round_completed(round_id, total_participants, total_tickets)

    async def update_round_status(self, round_id: int, status: str) -> None:
        await queries.update_lottery_round_status(round_id, status)

    async def add_entries(self, round_id: int, entries: List[Dict]) -> None:
        for e in entries:
            await queries.insert_lottery_round_entry(
                round_id,
                e["chat_id"],
                e["user_id"],
                e["checkin_days"],
                e["weight"],
                e.get("is_full_attendance", False),
                json.dumps(e.get("extra_info")) if e.get("extra_info") else None,
            )

    async def add_winners(self, round_id: int, winners: List[Dict]) -> None:
        for w in winners:
            await queries.insert_lottery_winner(
                round_id,
                w["chat_id"],
                w["user_id"],
                w.get("prize_set_id"),
                w["prize_name"],
                w.get("prize_description"),
                w.get("prize_rank", 1),
            )

    async def get_entries(self, round_id: int) -> List[Dict]:
        return await queries.get_entries_for_round(round_id)

    async def get_winners(self, round_id: int) -> List[Dict]:
        return await queries.get_winners_for_round(round_id)


class AdminActionRepository:
    async def log_action(self, chat_id: int, admin_user_id: int, action_type: str, payload: dict) -> None:
        payload_json = json.dumps(payload, ensure_ascii=False) if payload else None
        await queries.insert_admin_action(chat_id, admin_user_id, action_type, payload_json)

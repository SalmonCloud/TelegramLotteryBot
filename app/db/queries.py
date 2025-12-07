from datetime import date, datetime
from typing import Any, Dict, List, Optional
import asyncmy

from app.db.connection import get_db_pool


async def _execute(sql: str, params: tuple | list) -> int:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(sql, params)
            return cur.lastrowid


async def _fetchone(sql: str, params: tuple | list) -> Optional[Dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()


async def _fetchall(sql: str, params: tuple | list) -> List[Dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


# telegram_user
async def upsert_telegram_user(chat_id: int, user_id: int, username: str | None, first_name: str | None, last_name: str | None, is_bot: bool, language_code: str | None) -> None:
    sql = """
    INSERT INTO telegram_user (chat_id, user_id, username, first_name, last_name, is_bot, language_code)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        username = VALUES(username),
        first_name = VALUES(first_name),
        last_name = VALUES(last_name),
        is_bot = VALUES(is_bot),
        language_code = VALUES(language_code),
        updated_at = CURRENT_TIMESTAMP
    """
    await _execute(sql, (chat_id, user_id, username, first_name, last_name, int(is_bot), language_code))


# daily_checkins
async def insert_or_increment_daily_checkin(chat_id: int, user_id: int, checkin_date: date, message_id: int, message_time: datetime) -> None:
    sql = """
    INSERT INTO daily_checkins (chat_id, user_id, checkin_date, message_id, message_time)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        message_id = VALUES(message_id),
        message_time = VALUES(message_time),
        updated_at = CURRENT_TIMESTAMP
    """
    await _execute(sql, (chat_id, user_id, checkin_date, message_id, message_time))


async def get_user_checkin_for_date(chat_id: int, user_id: int, checkin_date: date) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT * FROM daily_checkins
    WHERE chat_id = %s AND user_id = %s AND checkin_date = %s
    LIMIT 1
    """
    return await _fetchone(sql, (chat_id, user_id, checkin_date))


async def count_user_checkins_between(chat_id: int, user_id: int, start_date: date, end_date: date) -> int:
    sql = """
    SELECT COUNT(*) AS cnt FROM daily_checkins
    WHERE chat_id = %s AND user_id = %s AND checkin_date BETWEEN %s AND %s
    """
    row = await _fetchone(sql, (chat_id, user_id, start_date, end_date))
    return int(row["cnt"]) if row else 0


async def count_distinct_users_for_date(chat_id: int, checkin_date: date) -> int:
    sql = """
    SELECT COUNT(DISTINCT user_id) AS cnt FROM daily_checkins
    WHERE chat_id = %s AND checkin_date = %s
    """
    row = await _fetchone(sql, (chat_id, checkin_date))
    return int(row["cnt"]) if row else 0


async def delete_checkins_before_date(chat_id: int, cutoff_date: date) -> int:
    sql = "DELETE FROM daily_checkins WHERE chat_id = %s AND checkin_date < %s"
    pool = get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(asyncmy.cursors.DictCursor) as cur:
            await cur.execute(sql, (chat_id, cutoff_date))
            return cur.rowcount


async def get_user_ids_for_date(chat_id: int, checkin_date: date) -> List[int]:
    sql = "SELECT DISTINCT user_id FROM daily_checkins WHERE chat_id = %s AND checkin_date = %s"
    rows = await _fetchall(sql, (chat_id, checkin_date))
    return [int(r["user_id"]) for r in rows]


async def get_weekly_checkin_counts_for_all_users(chat_id: int, start_date: date, end_date: date) -> Dict[int, int]:
    sql = """
    SELECT user_id, COUNT(*) AS cnt
    FROM daily_checkins
    WHERE chat_id = %s AND checkin_date BETWEEN %s AND %s
    GROUP BY user_id
    """
    rows = await _fetchall(sql, (chat_id, start_date, end_date))
    return {int(r["user_id"]): int(r["cnt"]) for r in rows}


# lottery_settings
async def get_lottery_settings(chat_id: int) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM lottery_settings WHERE chat_id = %s LIMIT 1"
    return await _fetchone(sql, (chat_id,))


async def insert_default_lottery_settings(chat_id: int, timezone: str) -> None:
    sql = """
    INSERT INTO lottery_settings (chat_id, weekly_enabled, weekly_draw_at, full_attendance_factor, timezone)
    VALUES (%s, 1, '00:00:00', 2, %s)
    ON DUPLICATE KEY UPDATE chat_id = chat_id
    """
    await _execute(sql, (chat_id, timezone))


async def update_weekly_enabled(chat_id: int, enabled: bool) -> None:
    sql = "UPDATE lottery_settings SET weekly_enabled = %s WHERE chat_id = %s"
    await _execute(sql, (int(enabled), chat_id))


async def update_draw_times(chat_id: int, weekly_time: str) -> None:
    sql = "UPDATE lottery_settings SET weekly_draw_at = %s WHERE chat_id = %s"
    await _execute(sql, (weekly_time, chat_id))


async def update_full_attendance_factor(chat_id: int, factor: int) -> None:
    sql = "UPDATE lottery_settings SET full_attendance_factor = %s WHERE chat_id = %s"
    await _execute(sql, (factor, chat_id))


# prize_sets / prize_items
async def get_prize_set_for_period(chat_id: int, set_type: str, period_start: date, period_end: date) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT * FROM prize_sets
    WHERE chat_id = %s
      AND set_type = %s
      AND valid_from <= %s
      AND (valid_to IS NULL OR valid_to >= %s)
    ORDER BY valid_from DESC, id DESC
    LIMIT 1
    """
    return await _fetchone(sql, (chat_id, set_type, period_start, period_end))


async def get_latest_prize_set_before(chat_id: int, set_type: str, ref_date: date) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT * FROM prize_sets
    WHERE chat_id = %s
      AND set_type = %s
      AND valid_from <= %s
    ORDER BY valid_from DESC, id DESC
    LIMIT 1
    """
    return await _fetchone(sql, (chat_id, set_type, ref_date))


async def insert_prize_set(chat_id: int, set_type: str, valid_from: date | None, valid_to: date | None) -> int:
    sql = """
    INSERT INTO prize_sets (chat_id, set_type, valid_from, valid_to)
    VALUES (%s, %s, %s, %s)
    """
    return await _execute(sql, (chat_id, set_type, valid_from, valid_to))


async def get_prize_items_for_set(set_id: int) -> List[Dict[str, Any]]:
    sql = """
    SELECT * FROM prize_items
    WHERE set_id = %s AND enabled = 1
    ORDER BY prize_rank ASC, id ASC
    """
    return await _fetchall(sql, (set_id,))


async def insert_prize_item(set_id: int, name: str, description: str | None, quantity: int, enabled: bool, prize_rank: int) -> None:
    sql = """
    INSERT INTO prize_items (set_id, name, description, quantity, enabled, prize_rank)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    await _execute(sql, (set_id, name, description, quantity, int(enabled), prize_rank))


async def update_prize_item_enabled(item_id: int, enabled: bool) -> None:
    sql = "UPDATE prize_items SET enabled = %s WHERE id = %s"
    await _execute(sql, (int(enabled), item_id))


# lottery_rounds
async def create_lottery_round(chat_id: int, round_type: str, period_start_date: date, period_end_date: date, draw_scheduled_at: datetime | None, note: str | None, prize_set_id: int | None) -> int:
    sql = """
    INSERT INTO lottery_rounds (chat_id, round_type, period_start_date, period_end_date, draw_scheduled_at, status, note, prize_set_id)
    VALUES (%s, %s, %s, %s, %s, 'running', %s, %s)
    """
    return await _execute(sql, (chat_id, round_type, period_start_date, period_end_date, draw_scheduled_at, note, prize_set_id))


async def mark_lottery_round_completed(round_id: int, total_participants: int, total_tickets: int) -> None:
    sql = """
    UPDATE lottery_rounds
    SET status = 'done', total_participants = %s, total_tickets = %s, completed_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """
    await _execute(sql, (total_participants, total_tickets, round_id))


async def update_lottery_round_status(round_id: int, status: str) -> None:
    sql = "UPDATE lottery_rounds SET status = %s WHERE id = %s"
    await _execute(sql, (status, round_id))


async def get_round_by_period(chat_id: int, round_type: str, period_start: date, period_end: date) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT * FROM lottery_rounds
    WHERE chat_id = %s AND round_type = %s AND period_start_date = %s AND period_end_date = %s
    LIMIT 1
    """
    return await _fetchone(sql, (chat_id, round_type, period_start, period_end))


# lottery_round_entries
async def insert_lottery_round_entry(round_id: int, chat_id: int, user_id: int, checkin_days: int, weight: int, is_full_attendance: bool, extra_info_json: str | None) -> None:
    sql = """
    INSERT INTO lottery_round_entries (round_id, chat_id, user_id, checkin_days, weight, is_full_attendance, extra_info_json)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        checkin_days = VALUES(checkin_days),
        weight = VALUES(weight),
        is_full_attendance = VALUES(is_full_attendance),
        extra_info_json = VALUES(extra_info_json),
        created_at = created_at
    """
    await _execute(sql, (round_id, chat_id, user_id, checkin_days, weight, int(is_full_attendance), extra_info_json))


async def get_entries_for_round(round_id: int) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM lottery_round_entries WHERE round_id = %s"
    return await _fetchall(sql, (round_id,))


# lottery_winners
async def insert_lottery_winner(round_id: int, chat_id: int, user_id: int, prize_set_id: int | None, prize_name: str, prize_description: str | None, prize_rank: int) -> None:
    sql = """
    INSERT INTO lottery_winners (round_id, chat_id, user_id, prize_set_id, prize_name, prize_description, prize_rank)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        prize_name = VALUES(prize_name),
        prize_description = VALUES(prize_description),
        prize_rank = VALUES(prize_rank),
        updated_at = CURRENT_TIMESTAMP
    """
    await _execute(sql, (round_id, chat_id, user_id, prize_set_id, prize_name, prize_description, prize_rank))


async def get_winners_for_round(round_id: int) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM lottery_winners WHERE round_id = %s ORDER BY prize_rank ASC, id ASC"
    return await _fetchall(sql, (round_id,))


async def update_winner_claim_status(winner_id: int, status: str) -> None:
    sql = "UPDATE lottery_winners SET claimed_status = %s, claimed_at = CASE WHEN %s='claimed' THEN CURRENT_TIMESTAMP ELSE claimed_at END WHERE id = %s"
    await _execute(sql, (status, status, winner_id))


# admin_actions
async def insert_admin_action(chat_id: int, admin_user_id: int, action_type: str, payload_json: str | None) -> None:
    sql = """
    INSERT INTO admin_actions (chat_id, admin_user_id, action_type, payload_json)
    VALUES (%s, %s, %s, %s)
    """
    await _execute(sql, (chat_id, admin_user_id, action_type, payload_json))

from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class CheckinStatusDTO:
    today_checked: bool
    week_checkin_count: int
    checkin_date: date


@dataclass
class LotteryEntryDTO:
    user_id: int
    checkin_days: int
    weight: int
    is_full_attendance: bool
    prize_rank: Optional[int] = None


@dataclass
class LotteryWinnerDTO:
    user_id: int
    prize_name: str
    prize_description: str
    prize_rank: int
    is_main_prize: bool = False


@dataclass
class LotteryResultDTO:
    round_id: int
    round_type: str
    period_start_date: date
    period_end_date: date
    total_participants: int
    total_tickets: int
    winners: List[LotteryWinnerDTO]

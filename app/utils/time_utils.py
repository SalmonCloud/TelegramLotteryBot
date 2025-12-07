from datetime import datetime, date, timedelta
import pytz

BEIJING_TZ = pytz.timezone("Asia/Shanghai")


def to_beijing(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(BEIJING_TZ)


def get_today_beijing(now: datetime | None = None) -> date:
    now = now or datetime.utcnow()
    return to_beijing(now).date()


def get_yesterday_beijing(now: datetime | None = None) -> date:
    return get_today_beijing(now) - timedelta(days=1)


def get_week_start_end(target_date: date) -> tuple[date, date]:
    start = target_date - timedelta(days=target_date.weekday())
    end = start + timedelta(days=6)
    return start, end

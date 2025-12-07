import os
from dataclasses import dataclass


@dataclass
class BotConfig:
    token: str
    target_chat_id: int


@dataclass
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class SchedulerConfig:
    enabled: bool = True
    timezone: str = "Asia/Shanghai"
    weekly_draw_at: str = "00:00"


@dataclass
class Config:
    bot: BotConfig
    db: DbConfig
    scheduler: SchedulerConfig
    target_chat_id: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "")
    target_chat_id = int(os.getenv("TARGET_CHAT_ID", "0"))

    db = DbConfig(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "LotteryBot"),
    )

    scheduler = SchedulerConfig(
        enabled=os.getenv("SCHEDULER_ENABLED", "true").lower() != "false",
        timezone=os.getenv("SCHEDULER_TZ", "Asia/Shanghai"),
        weekly_draw_at=os.getenv("WEEKLY_DRAW_AT", "00:00"),
    )

    bot_cfg = BotConfig(token=token, target_chat_id=target_chat_id)

    return Config(bot=bot_cfg, db=db, scheduler=scheduler, target_chat_id=target_chat_id)

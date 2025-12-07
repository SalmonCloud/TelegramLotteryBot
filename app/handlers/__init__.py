from aiogram import Dispatcher

from app.handlers import user_message, user_common, admin_lottery, admin_prize, admin_maintenance, errors
from app.config import Config


def register_handlers(dp: Dispatcher, config: Config) -> None:
    user_message.register_user_message_handlers(dp, config)
    user_common.register_user_common_handlers(dp, config)
    admin_lottery.register_admin_lottery_handlers(dp, config)
    admin_prize.register_admin_prize_handlers(dp, config)
    admin_maintenance.register_admin_maintenance_handlers(dp, config)
    errors.register_error_handlers(dp)

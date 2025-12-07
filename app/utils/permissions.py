from aiogram import Bot


async def is_chat_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        admins = await bot.get_chat_administrators(chat_id)
    except Exception:
        return False
    for member in admins:
        if member.user.id == user_id:
            return True
    return False

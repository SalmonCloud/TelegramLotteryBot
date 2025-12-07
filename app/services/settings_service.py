from app.db.repositories import SettingsRepository


class SettingsService:
    def __init__(self, repo: SettingsRepository, timezone: str = "Asia/Shanghai"):
        self.repo = repo
        self.timezone = timezone

    async def get_settings(self, chat_id: int):
        return await self.repo.get_or_create_settings(chat_id, self.timezone)

    async def set_weekly_enabled(self, chat_id: int, enabled: bool) -> None:
        await self.repo.set_weekly_enabled(chat_id, enabled)

    async def is_weekly_enabled(self, chat_id: int) -> bool:
        settings = await self.get_settings(chat_id)
        return bool(settings.get("weekly_enabled", 0))

    async def get_draw_times(self, chat_id: int) -> dict:
        settings = await self.get_settings(chat_id)
        return {
            "weekly": settings.get("weekly_draw_at"),
        }

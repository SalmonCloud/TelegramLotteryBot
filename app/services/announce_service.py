import logging

from app.models.dto import LotteryResultDTO
from app.texts import zh_cn


class AnnounceService:
    def __init__(self, bot):
        self.bot = bot

    async def send_daily_stats(self, chat_id: int, date, user_count: int) -> None:
        text = zh_cn.TEXT_DAILY_STATS.format(date=date, user_count=user_count)
        await self.bot.send_message(chat_id=chat_id, text=text)

    async def send_weekly_lottery_result(self, chat_id: int, result: LotteryResultDTO) -> None:
        lines = [
            "🎉 周抽奖结果",
            "━━━━━━━━━━━━",
            f"📅 周期：{result.period_start_date} ~ {result.period_end_date}",
            f"👥 参与人数：{result.total_participants}",
            f"🎟️ 总权重：{result.total_tickets}",
            "━━━━━━━━━━━━",
            "🏆 中奖名单：",
        ]
        if not result.winners:
            lines.append("🙈 本期无人中奖")
        else:
            for w in result.winners:
                user_tag = await self._format_user(chat_id, w.user_id)
                lines.append(f"{self._medal_for_rank(w.prize_rank)} #{w.prize_rank} {user_tag} - {w.prize_name}")
        await self.bot.send_message(chat_id=chat_id, text="\n".join(lines))

    async def send_new_member_welcome(self, chat_id: int, user_id: int) -> None:
        text = zh_cn.TEXT_NEW_MEMBER_WELCOME
        await self.bot.send_message(chat_id=chat_id, text=text)

    async def _format_user(self, chat_id: int, user_id: int) -> str:
        try:
            member = await self.bot.get_chat_member(chat_id, user_id)
            user = getattr(member, "user", None)
            if user and user.username:
                return f"@{user.username}"
            if user:
                name_parts = [user.first_name or "", user.last_name or ""]
                name = " ".join(part for part in name_parts if part).strip()
                if name:
                    return name
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to resolve username for user_id=%s: %s", user_id, e)
        return f"用户 {user_id}"

    def _medal_for_rank(self, rank: int | None) -> str:
        if rank == 1:
            return "🥇"
        if rank == 2:
            return "🥈"
        if rank == 3:
            return "🥉"
        return "🏅"

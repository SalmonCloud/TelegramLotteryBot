TEXT_CHECKIN_SUCCESS = "✅ 已打卡：{date}，本周累计 {week_count} 天，加油保持！"
TEXT_CHECKIN_NOT_FOUND = "⚠️ 今日尚未打卡（{date}），本周累计 {week_count} 天，快发一条消息完成打卡吧！"
TEXT_DAILY_STATS = "昨日（{date}）共有 {user_count} 人打卡。"
TEXT_WEEKLY_LOTTERY_HEADER = "周抽奖结果\n周期：{period}\n参与人数：{participants}\n总权重：{tickets}"
TEXT_LOTTERY_INFO = (
    "🎯 抽奖详情\n"
    "📊 状态：{status}\n"
    "🕒 抽奖时间：{weekly_draw_at} (北京时间)\n"
    "🎁 奖池：\n{prize_lines}\n"
    "📦 奖品总数：{prize_total} 个\n"
    "👥 已具备抽奖资格人数：{qualified_count} 人\n"
    "------\n"
    "打卡抽奖规则如下：\n"
    "💡 发送任意非命令消息即可完成今日打卡\n"
    "{weight_note}"
)
TEXT_NOT_ADMIN = "你不是管理员，无权使用此命令。"
TEXT_TOO_FREQUENT = "操作过于频繁，请稍后再试。"
TEXT_WEEKLY_LOTTERY_PAUSED = "已暂停周抽奖。"
TEXT_WEEKLY_LOTTERY_RESUMED = "已恢复周抽奖。"
TEXT_NEW_MEMBER_WELCOME = "欢迎加入！在群里发消息即可每日打卡，每周自动抽奖。"
TEXT_WEEKLY_LOTTERY_DISABLED = "⚠️ 周抽奖已暂停，无法查看周奖池。"
TEXT_WEEKLY_LOTTERY_STATUS = "周抽奖状态：{status}"
TEXT_LAST_WEEKLY_RESULT_NOT_FOUND = "未找到上一期周抽奖结果。"


def render_prize_list(title: str, prizes) -> str:
    lines = [title]
    for p in prizes or []:
        lines.append(f"#{p.get('prize_rank', '?')} {p.get('name')} x{p.get('quantity', 1)}")
    return "\n".join(lines)

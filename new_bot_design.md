# LotteryBot 抽奖机器人设计文档（单群版，周抽奖）

> 现状与范围  
> - 仅服务一个 Telegram 群组，`TARGET_CHAT_ID` 配置给定。  
> - 功能：每日打卡、周抽奖（上一周数据开奖）、上一期结果查询、奖池按周周期滚动（valid_from/valid_to），自动克隆上一周奖池。  
> - 技术栈：Python 3.10+，aiogram v3，MySQL（schema: LotteryBot），APScheduler。  
> - 已移除日抽奖相关逻辑与列，抽奖仅保留周抽。  

---

## 1. 抽奖与打卡规则
- 打卡：群内非命令消息（排除机器人、斜杠命令）即记为当日打卡，同一日同一人只记一次。日期按北京时间计算。
- 周抽奖：开奖周期为上一周（周一至周日），权重 = 打卡天数；满勤（7 天）权重 × 全勤系数（默认 2）。
- 奖池：按周有效期 `valid_from/valid_to` 管理。若本周奖池缺失，会自动克隆最近一期奖池并提示管理员。
- 中奖公告：群内发布，展示可点击的 @username；无人中奖时提示。
- 幂等：同一周期只开奖一次；已有完成记录则直接返回历史结果。

---

## 2. 数据模型（主要表）
- `daily_checkins`：打卡记录 `(chat_id, user_id, checkin_date, message_id, message_time)`；唯一 `(chat_id, user_id, checkin_date)`。
- `lottery_settings`：群配置，仅周抽相关字段（weekly_enabled、weekly_draw_at、full_attendance_factor、timezone）。
- `prize_sets`：奖池集合，字段含 `set_type='weekly'`，`valid_from/valid_to`，以及时间戳；不再使用 phase/current/next，也不再存 title/description/created_by。
- `prize_items`：具体奖品，含 `quantity`、`prize_rank`、`enabled`（已移除 priority_order）。
- `lottery_rounds`：抽奖轮次（`round_type='weekly'`），记录周期起止、状态、参与/权重统计、关联奖池。
- `lottery_round_entries`：某轮次的参与快照（用户、权重、满勤标记、extra_info）。
- `lottery_winners`：中奖结果（含 `prize_rank`）。
- `admin_actions`：管理员操作日志。

---

## 3. 目录与模块
- 入口：`run_bot.py`（加载配置/日志，初始化 Bot/DP/Scheduler，注册 handler/middleware/jobs，启动时检查本周奖池并提醒管理员）。
- 配置：`app/config.py`（Token、DB、TARGET_CHAT_ID、时区、周抽时间等）；`.env` 示例不再包含日抽字段。
- DB 访问：`app/db/connection.py`、`queries.py`、`repositories.py`。
- 服务：
  - `CheckinService`：打卡处理/统计。
  - `SettingsService`：周抽开关、时间、全勤系数。
  - `PrizeService`：按周期取奖池、获取某周奖池、克隆上一周奖池。
  - `LotteryService`：周抽逻辑（上一周数据开奖）、上一期结果获取、中奖写表、自动预生成下一周奖池（如缺失）。
  - `AnnounceService`：公告格式（表情、分隔线、@username）。
  - `StatsService`：打卡统计。
- Handler：
  - 用户：`/check_checkin`、`/lottery_info`、`/last_weekly_lottery_result`、`/ping`。
  - 管理员：`/weekly_lottery_pause` `/weekly_lottery_resume` `/draw_now_weekly` `/show_weekly_prizes` `/cleanup_checkins` `/stats_today` `/stats_week` `/admin_ping`。
  - 群消息打卡：过滤机器人/命令。
  - 错误处理：统一日志。
- 中间件：服务注入、命令日志。
- Scheduler：每日统计（昨日打卡数）、周抽奖（检查开关与幂等）。
- 文案：`app/texts/zh_cn.py`。

---

## 4. 奖池滚动策略
- 仅周抽奖使用 `valid_from/valid_to`。当前周查询：`valid_from <= 周起始 <= valid_to`。
- 开奖时如找不到本周奖池：尝试克隆最近一期奖池生成本周奖池；若仍不存在则抛错。
- 开奖完成后：若下一周奖池不存在，自动克隆本周奖池生成下一周奖池。
- 启动时：检查本周奖池是否存在，不存在则在群内提醒管理员手动配置。

---

## 5. 命令与可见性
- 用户命令（默认作用域）：`/check_checkin`、`/lottery_info`、`/last_weekly_lottery_result`、`/ping`。
- 管理员命令（群管理员作用域）：`/weekly_lottery_pause` `/weekly_lottery_resume` `/draw_now_weekly` `/show_weekly_prizes` `/cleanup_checkins` `/stats_today` `/stats_week` `/admin_ping`。
- 日抽奖相关命令/字段已移除。

---

## 6. 抽奖公告格式
- 周抽结果：
  - 标题 + 分隔线
  - 周期、参与人数、总权重
  - 分隔线
  - 中奖名单（🥇🥈🥉/🏅 + @username 可点击；无人中奖时提示）
- `/lottery_info`：
  - 状态、开奖时间、奖池列表、奖品总数
  - 分隔线
  - 打卡提示 + 权重说明（满勤系数）

---

## 7. 迁移提示
- 删除日抽奖列（lottery_settings）：`daily_enabled`, `daily_draw_at`, `daily_weight_mode`（代码已不再引用）。
- 逐步弃用 prize_sets.phase（已不用）；奖池按 `valid_from/valid_to` 周期查询；title/description/created_by 已移除；prize_items 取消 priority_order。
- 确保 lottery_winners 表含 `prize_rank` 字段。  

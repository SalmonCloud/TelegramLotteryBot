-- LotteryBot database DDL (MySQL 8+)
-- All datetimes stored in UTC; business logic converts to Beijing time when needed.

CREATE SCHEMA IF NOT EXISTS `LotteryBot` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `LotteryBot`;

-- Telegram users per chat
CREATE TABLE IF NOT EXISTS `telegram_user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chat_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `username` VARCHAR(255) NULL,
  `first_name` VARCHAR(255) NULL,
  `last_name` VARCHAR(255) NULL,
  `is_bot` TINYINT(1) NOT NULL DEFAULT 0,
  `language_code` VARCHAR(16) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_telegram_user_chat_user` (`chat_id`, `user_id`),
  KEY `idx_telegram_user_chat` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Daily check-ins (one row per user per Beijing date)
CREATE TABLE IF NOT EXISTS `daily_checkins` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chat_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `checkin_date` DATE NOT NULL,
  `message_id` BIGINT NULL,
  `message_time` DATETIME NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_daily_checkins_chat_user_date` (`chat_id`, `user_id`, `checkin_date`),
  KEY `idx_daily_checkins_chat_date` (`chat_id`, `checkin_date`),
  KEY `idx_daily_checkins_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Settings (single row for the target chat, but schema allows more)
CREATE TABLE IF NOT EXISTS `lottery_settings` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chat_id` BIGINT NOT NULL,
  `weekly_enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `daily_enabled` TINYINT(1) NOT NULL DEFAULT 0,
  `weekly_draw_at` TIME NOT NULL DEFAULT '00:00:00',
  `daily_draw_at` TIME NOT NULL DEFAULT '21:00:00',
  `daily_weight_mode` ENUM('fixed', 'weekly_accum') NOT NULL DEFAULT 'fixed',
  `full_attendance_factor` INT NOT NULL DEFAULT 2,
  `timezone` VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lottery_settings_chat` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Prize sets (current / next / archived per type)
CREATE TABLE IF NOT EXISTS `prize_sets` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chat_id` BIGINT NOT NULL,
  `set_type` ENUM('weekly', 'daily', 'custom') NOT NULL,
  `phase` ENUM('current', 'next', 'archived') NOT NULL DEFAULT 'current',
  `title` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `valid_from` DATE NULL,
  `valid_to` DATE NULL,
  `created_by` BIGINT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_prize_sets_chat_type_phase` (`chat_id`, `set_type`, `phase`),
  KEY `idx_prize_sets_chat_type` (`chat_id`, `set_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Prize items under a prize set
CREATE TABLE IF NOT EXISTS `prize_items` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `set_id` BIGINT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  `enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `prize_rank` INT NOT NULL DEFAULT 1, -- 1 = 最高奖，数字越大等级越低
  `priority_order` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_prize_items_set` (`set_id`),
  UNIQUE KEY `uq_prize_items_set_rank` (`set_id`, `prize_rank`),
  KEY `idx_prize_items_order` (`priority_order`),
  CONSTRAINT `fk_prize_items_set` FOREIGN KEY (`set_id`) REFERENCES `prize_sets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lottery rounds (enforces one round per chat/type/period)
CREATE TABLE IF NOT EXISTS `lottery_rounds` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chat_id` BIGINT NOT NULL,
  `round_type` ENUM('weekly', 'daily', 'custom') NOT NULL,
  `period_start_date` DATE NOT NULL,
  `period_end_date` DATE NOT NULL,
  `draw_scheduled_at` DATETIME NULL,
  `started_at` DATETIME NULL,
  `completed_at` DATETIME NULL,
  `status` ENUM('pending', 'running', 'done', 'cancelled') NOT NULL DEFAULT 'pending',
  `prize_set_id` BIGINT UNSIGNED NULL,
  `total_participants` INT NULL,
  `total_tickets` INT NULL,
  `note` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lottery_rounds_chat_type_period` (`chat_id`, `round_type`, `period_start_date`, `period_end_date`),
  KEY `idx_lottery_rounds_status` (`status`),
  CONSTRAINT `fk_lottery_rounds_prize_set` FOREIGN KEY (`prize_set_id`) REFERENCES `prize_sets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lottery entries per round (weights, attendance info)
CREATE TABLE IF NOT EXISTS `lottery_round_entries` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `round_id` BIGINT UNSIGNED NOT NULL,
  `chat_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `checkin_days` INT NOT NULL,
  `weight` INT NOT NULL,
  `is_full_attendance` TINYINT(1) NOT NULL DEFAULT 0,
  `extra_info_json` JSON NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lottery_entries_round_user` (`round_id`, `user_id`),
  KEY `idx_lottery_entries_round` (`round_id`),
  KEY `idx_lottery_entries_chat` (`chat_id`),
  CONSTRAINT `fk_lottery_entries_round` FOREIGN KEY (`round_id`) REFERENCES `lottery_rounds` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Winners per round
CREATE TABLE IF NOT EXISTS `lottery_winners` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `round_id` BIGINT UNSIGNED NOT NULL,
  `chat_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `prize_set_id` BIGINT UNSIGNED NULL,
  `prize_name` VARCHAR(255) NOT NULL,
  `prize_description` TEXT NULL,
  `prize_rank` INT NOT NULL DEFAULT 1, -- 1 = 最高奖
  `claimed_status` ENUM('pending', 'claimed', 'expired') NOT NULL DEFAULT 'pending',
  `claimed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lottery_winners_round_user` (`round_id`, `user_id`),
  KEY `idx_lottery_winners_round` (`round_id`),
  KEY `idx_lottery_winners_prize_set` (`prize_set_id`),
  CONSTRAINT `fk_lottery_winners_round` FOREIGN KEY (`round_id`) REFERENCES `lottery_rounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_lottery_winners_prize_set` FOREIGN KEY (`prize_set_id`) REFERENCES `prize_sets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admin actions audit log
CREATE TABLE IF NOT EXISTS `admin_actions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chat_id` BIGINT NOT NULL,
  `admin_user_id` BIGINT NOT NULL,
  `action_type` VARCHAR(64) NOT NULL,
  `payload_json` JSON NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_admin_actions_chat` (`chat_id`),
  KEY `idx_admin_actions_type` (`action_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

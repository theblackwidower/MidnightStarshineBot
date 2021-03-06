  -- ------------------------------------------------------------------------
  -- MidnightStarshineBot - a multipurpose Discord bot
  -- Copyright (C) 2020  T. Duke Perry
  --
  -- This program is free software: you can redistribute it and/or modify
  -- it under the terms of the GNU Affero General Public License as published
  -- by the Free Software Foundation, either version 3 of the License, or
  -- (at your option) any later version.
  --
  -- This program is distributed in the hope that it will be useful,
  -- but WITHOUT ANY WARRANTY; without even the implied warranty of
  -- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  -- GNU Affero General Public License for more details.
  --
  -- You should have received a copy of the GNU Affero General Public License
  -- along with this program.  If not, see <https://www.gnu.org/licenses/>.
  -- ------------------------------------------------------------------------

CREATE TABLE "tbl_prefix" (
  "server" BIGINT NOT NULL PRIMARY KEY,
  "prefix" TEXT NOT NULL
);

CREATE TABLE "tbl_currency" (
  "server" BIGINT PRIMARY KEY,
  "currency_name" TEXT NOT NULL
);

CREATE TABLE "tbl_payday_settings" (
  "server" BIGINT PRIMARY KEY,
  "amount" INTEGER NOT NULL,
  "cooldown" INTERVAL NOT NULL
);

CREATE TABLE "tbl_paid_roles" (
  "server" BIGINT NOT NULL,
  "role" BIGINT NOT NULL,
  "cost" INTEGER NOT NULL,
  PRIMARY KEY("server", "role")
);

CREATE TABLE "tbl_account_balance" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "balance" INTEGER NOT NULL,
  "last_payday" TIMESTAMP,
  PRIMARY KEY("server", "member")
);

CREATE TABLE "tbl_purchase_record" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "role" BIGINT NOT NULL,
  "amount_paid" INTEGER NOT NULL,
  PRIMARY KEY("server", "member", "role")
);

CREATE TABLE "tbl_rules" (
  "id" SERIAL PRIMARY KEY,
  "server" BIGINT NOT NULL,
  "content" TEXT NOT NULL
);

CREATE TABLE "tbl_rule_posting" (
  "server" BIGINT PRIMARY KEY,
  "channel" BIGINT NOT NULL UNIQUE,
  "message" BIGINT UNIQUE
);

CREATE TABLE "tbl_active_role_settings" (
  "server" BIGINT PRIMARY KEY,
  "role" BIGINT NOT NULL UNIQUE,
  "gap" INTERVAL NOT NULL,
  "duration" INTERVAL NOT NULL,
  "max" INTERVAL NOT NULL
);

CREATE TABLE "tbl_activity_record" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "last_active" TIMESTAMP NOT NULL,
  PRIMARY KEY("server", "member")
);

CREATE TABLE "tbl_promoter_role_settings" (
  "server" BIGINT NOT NULL,
  "role" BIGINT NOT NULL UNIQUE,
  "recruit_count" INTEGER NOT NULL,
  PRIMARY KEY("server", "recruit_count")
);

CREATE TABLE "tbl_recruitment_record" (
  "server" BIGINT NOT NULL,
  "recruiter" BIGINT NOT NULL,
  "recruited_member" BIGINT NOT NULL,
  PRIMARY KEY("server", "recruited_member"),
  CHECK("recruiter" <> "recruited_member")
);

CREATE TABLE "tbl_bumper_role_settings" (
  "server" BIGINT NOT NULL,
  "role" BIGINT NOT NULL UNIQUE,
  "bump_count" INTEGER NOT NULL,
  PRIMARY KEY("server", "bump_count")
);

CREATE TABLE "tbl_bumping_record" (
  "server" BIGINT NOT NULL,
  "bumper" BIGINT NOT NULL,
  "response_id" BIGINT NOT NULL PRIMARY KEY,
  "timebumped" TIMESTAMP NOT NULL
);

CREATE TABLE "tbl_bump_leaderboard_posting" (
  "server" BIGINT PRIMARY KEY,
  "channel" BIGINT NOT NULL UNIQUE,
  "message" BIGINT UNIQUE
);

CREATE TABLE "tbl_role_groups" (
  "server" BIGINT NOT NULL,
  "group_name" TEXT NOT NULL,
  PRIMARY KEY("server", "group_name")
);

CREATE TABLE "tbl_controlled_roles" (
  "server" BIGINT NOT NULL,
  "group_name" TEXT NOT NULL,
  "role" BIGINT PRIMARY KEY,
  FOREIGN KEY ("server", "group_name") REFERENCES tbl_role_groups
);

CREATE TABLE "tbl_mute_roles" (
  "server" BIGINT NOT NULL PRIMARY KEY,
  "role" BIGINT NOT NULL
);

CREATE TABLE "tbl_muted_members" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "channel" BIGINT DEFAULT 0,
  PRIMARY KEY("server", "member", "channel")
);

CREATE TABLE "tbl_timeout_channel" (
  "server" BIGINT NOT NULL PRIMARY KEY,
  "channel" BIGINT NOT NULL
);

CREATE TABLE "tbl_timeout_roles" (
  "server" BIGINT NOT NULL PRIMARY KEY,
  "role" BIGINT NOT NULL
);

CREATE TABLE "tbl_timedout_members" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  PRIMARY KEY("server", "member")
);

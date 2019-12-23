  -- ------------------------------------------------------------------------
  -- MidnightStarshineBot - a multipurpose Discord bot
  -- Copyright (C) 2019  T. Duke Perry
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

CREATE TABLE "tbl_accounts" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "funds" INTEGER NOT NULL,
  -- Will last until January 19 2038 03:14:07 UTC
  "last_payday" INTEGER,
  PRIMARY KEY("server", "member")
);

CREATE TABLE "tbl_currency" (
  "server" BIGINT PRIMARY KEY,
  "currency_name" TEXT NOT NULL
);

CREATE TABLE "tbl_payday_settings" (
  "server" BIGINT PRIMARY KEY,
  "amount" INTEGER NOT NULL,
  "cooldown" INTEGER NOT NULL
);

CREATE TABLE "tbl_paid_roles" (
  "server" BIGINT NOT NULL,
  "role" BIGINT NOT NULL,
  "cost" INTEGER NOT NULL,
  PRIMARY KEY("server", "role")
);

CREATE TABLE "tbl_transactions" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "date" INTEGER NOT NULL,
  "amount_in" INTEGER NOT NULL,
  "notes" TEXT,
  PRIMARY KEY("server", "member", "date")
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
  "gap" INTEGER NOT NULL,
  "duration" INTEGER NOT NULL,
  "max" INTEGER NOT NULL
);

CREATE TABLE "tbl_activity_record" (
  "server" BIGINT NOT NULL,
  "member" BIGINT NOT NULL,
  "last_active" INTEGER NOT NULL,
  PRIMARY KEY("server", "member")
);

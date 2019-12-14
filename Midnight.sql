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

CREATE TABLE "tbl_currency" (
	"server_id"	INTEGER NOT NULL,
	"member_id"	INTEGER NOT NULL,
	"funds"	INTEGER NOT NULL,
	"last_payday"	INTEGER,
	PRIMARY KEY("server_id","member_id")
);

CREATE TABLE "tbl_rules" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"server"	INTEGER NOT NULL,
	"content"	TEXT NOT NULL
);

CREATE TABLE "tbl_rule_posting" (
	"server"	INTEGER NOT NULL UNIQUE,
	"channel"	INTEGER NOT NULL UNIQUE,
	"message"	INTEGER UNIQUE,
	PRIMARY KEY("server")
);

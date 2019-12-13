CREATE TABLE "tbl_currency" (
	"server_id"	INTEGER,
	"member_id"	INTEGER,
	"funds"	INTEGER,
	"last_payday"	INTEGER,
	PRIMARY KEY("server_id","member_id")
);

CREATE TABLE "tbl_rules" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"server"	INTEGER NOT NULL,
	"content"	TEXT NOT NULL
);

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

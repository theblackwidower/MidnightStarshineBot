CREATE TABLE "tbl_currency" (
	"server_id"	INTEGER,
	"member_id"	INTEGER,
	"funds"	INTEGER,
	"last_payday"	INTEGER,
	PRIMARY KEY("server_id","member_id")
);

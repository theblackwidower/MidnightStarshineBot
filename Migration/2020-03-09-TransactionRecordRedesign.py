    # ------------------------------------------------------------------------
    # MidnightStarshineBot - a multipurpose Discord bot
    # Copyright (C) 2020  T. Duke Perry
    #
    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU Affero General Public License as published
    # by the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.
    #
    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU Affero General Public License for more details.
    #
    # You should have received a copy of the GNU Affero General Public License
    # along with this program.  If not, see <https://www.gnu.org/licenses/>.
    # ------------------------------------------------------------------------

# On March 7, 2020. I redesigned the back end of the economy feature so only a summary of the accont record is stored in the database and transaction records are stored in external files.
# This file is meant to be run only once to convert a pre-existing database from the old system to the new system.
# It also tests for data integrity.
# But if something goes wrong, it will not attempt to undo what has already been done.
# Because of this, it is recommended that you backup the database before running this file.

import discord

import os
import datetime
import asyncpg
import asyncio

from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

TRANSACTION_PAYDAY = "Payday"
TRANSACTION_BUY_ROLE = "Buying Role"
TRANSACTION_REFUND_ROLE = "Refunding Role"

discordConnection = discord.Client()

async def migrate():
    try:
        print("Migrating...")
        conn = await asyncpg.connect(DATABASE_URL)

        await conn.execute('CREATE TABLE tbl_account_balance (server BIGINT NOT NULL, member BIGINT NOT NULL, balance INTEGER NOT NULL, last_payday TIMESTAMP, PRIMARY KEY(server, member))')
        await conn.execute('INSERT INTO tbl_account_balance (server, member, balance) SELECT server, member, SUM(amount_in) FROM tbl_transactions GROUP BY server, member')
        cooldownRecords = await conn.fetch('SELECT MAX(date), server, member FROM tbl_transactions WHERE notes = \'' + TRANSACTION_PAYDAY + '\' GROUP BY server, member')
        await conn.executemany('UPDATE tbl_account_balance SET last_payday = $1 WHERE server = $2 AND member = $3', cooldownRecords)

        await conn.execute('CREATE TABLE tbl_purchase_record (server BIGINT NOT NULL, member BIGINT NOT NULL, role BIGINT NOT NULL, amount_paid INTEGER NOT NULL, PRIMARY KEY(server, member, role))')
        saleRecords = await conn.fetch('SELECT server, member, notes, amount_in FROM tbl_transactions WHERE (notes LIKE \'' + TRANSACTION_BUY_ROLE + ': %(%)\' OR notes LIKE \'' + TRANSACTION_REFUND_ROLE + ': %(%)\') ORDER BY date')
        netRecords = dict()
        for row in saleRecords:
            parsing = row[2].rpartition("(")
            roleId = int(parsing[2][:len(parsing[2]) - 1])

            if row[2].startswith(TRANSACTION_BUY_ROLE):
                if (row[0], row[1], roleId) in netRecords:
                    raise Exception("Data integrity error. Role bought twice: " + str(row[0]) + ", " + str(row[1]) + ", " + str(roleId))
                else:
                    netRecords[row[0], row[1], roleId] = -row[3]

            elif row[2].startswith(TRANSACTION_REFUND_ROLE):
                if (row[0], row[1], roleId) not in netRecords:
                    raise Exception("Data integrity error. Unbought role refunded: " + str(row[0]) + ", " + str(row[1]) + ", " + str(roleId))
                elif netRecords[row[0], row[1], roleId] != row[3]:
                    raise Exception("Data integrity error. Role refunded at the wrong price: " + str(row[0]) + ", " + str(row[1]) + ", " + str(roleId) + ", " + str(netRecords[row[0], row[1], roleId]) + ", " + str(row[3]))
                else:
                    del netRecords[row[0], row[1], roleId]
            else:
                raise Exception("Data integrity error. Incorrect note tag used: " + row[2])

        finalSubmission = []
        for server, member, role in netRecords.keys():
            amount_paid = netRecords[server, member, role]
            finalSubmission.append((server, member, role, amount_paid))

        await conn.executemany('INSERT INTO tbl_purchase_record (server, member, role, amount_paid) VALUES ($1, $2, $3, $4)', finalSubmission)

        print("Testing...")

        user_list = await conn.fetch('SELECT DISTINCT server, member FROM tbl_transactions')
        role_db_list = await conn.fetch('SELECT DISTINCT notes FROM tbl_transactions WHERE notes LIKE \'' + TRANSACTION_BUY_ROLE + ': %(%)\' OR notes LIKE \'' + TRANSACTION_REFUND_ROLE + ': %(%)\'')
        role_list = []
        for row in role_db_list:
            parsing = row[0].rpartition("(")
            roleId = int(parsing[2][:len(parsing[2]) - 1])
            if roleId not in role_list:
                role_list.append(roleId)

        server_list = []
        for row in user_list:
            serverId = row[0]
            memberId = row[1]

            if serverId not in server_list:
                server_list.append(serverId)

            oldFundsData = await conn.fetchrow('SELECT SUM(amount_in) FROM tbl_transactions WHERE server = $1 AND member = $2', serverId, memberId)
            oldCooldownData = await conn.fetchrow('SELECT MAX(date) FROM tbl_transactions WHERE server = $1 AND member = $2 AND notes = $3', serverId, memberId, TRANSACTION_PAYDAY)
            if oldFundsData is not None or oldCooldownData is not None:
                newAccountData = await conn.fetchrow('SELECT balance, last_payday FROM tbl_account_balance WHERE server = $1 AND member = $2', serverId, memberId)
                if newAccountData is None:
                    message = "Migration error in tbl_account_balance.\n"
                    message += "server: " + str(serverId) + "\n"
                    message += "member: " + str(memberId) + "\n"
                    if oldFundsData is not None:
                        message += "oldFundsData: " + str(oldFundsData[0]) + "\n"
                    if oldCooldownData is not None:
                        message += "oldCooldownData: " + str(oldCooldownData[0]) + "\n"
                    message += "missing data."
                    raise Exception(message)
                elif oldFundsData[0] != newAccountData[0]:
                    message = "Migration error in tbl_account_balance.\n"
                    message += "server: " + str(serverId) + "\n"
                    message += "member: " + str(memberId) + "\n"
                    message += "old currentFunds data: " + str(oldFundsData[0]) + "\n"
                    message += "new currentFunds data: " + str(newAccountData[0])
                    raise Exception(message)
                elif oldCooldownData[0] != newAccountData[1]:
                    message = "Migration error in tbl_account_balance.\n"
                    message += "server: " + str(serverId) + "\n"
                    message += "member: " + str(memberId) + "\n"
                    message += "old lastPayday data: " + str(oldCooldownData[0]) + "\n"
                    message += "new lastPayday data: " + str(newAccountData[1])
                    raise Exception(message)

            for roleId in role_list:
                newCostData = await conn.fetchrow('SELECT amount_paid FROM tbl_purchase_record WHERE server = $1 AND member = $2 AND role = $3', serverId, memberId, roleId)
                if newCostData is not None:
                    oldCostData = await conn.fetchrow('SELECT amount_in FROM tbl_transactions WHERE server = $1 AND member = $2 AND notes LIKE $3 ORDER BY date DESC', serverId, memberId, TRANSACTION_BUY_ROLE + ": %(" + str(roleId) + ")")
                    if oldCostData is None:
                        message = "Migration error in tbl_purchase_record.\n"
                        message += "server: " + str(serverId) + "\n"
                        message += "member: " + str(memberId) + "\n"
                        message += "role: " + str(roleId) + "\n"
                        message += "missing data in original."
                        raise Exception(message)
                    elif -oldCostData[0] != newCostData[0]:
                        message = "Migration error in tbl_purchase_record.\n"
                        message += "server: " + str(serverId) + "\n"
                        message += "member: " + str(memberId) + "\n"
                        message += "role: " + str(roleId) + "\n"
                        message += "old cost data: " + str(-oldCostData[0]) + "\n"
                        message += "new cost data: " + str(newCostData[0])
                        raise Exception(message)

                oldTransactionData = await conn.fetch('SELECT member, notes FROM tbl_transactions WHERE server = $1 AND (notes LIKE $2 OR notes LIKE $3) ORDER BY date', serverId, TRANSACTION_BUY_ROLE + ": %(" + str(roleId) + ")", TRANSACTION_REFUND_ROLE + ": %(" + str(roleId) + ")")
                if oldTransactionData is not None:
                    oldPaidMembers = []
                    for row in oldTransactionData:
                        member = row[0]
                        note = row[1]
                        if note.startswith(TRANSACTION_BUY_ROLE):
                            oldPaidMembers.append(member)
                        elif note.startswith(TRANSACTION_REFUND_ROLE):
                            oldPaidMembers.remove(member)
                    for memberId in oldPaidMembers:
                        newTransactionData = await conn.fetchrow('SELECT amount_paid FROM tbl_purchase_record WHERE server = $1 AND role = $2 AND member = $3', serverId, roleId, memberId)
                        if newTransactionData is None:
                            message = "Migration error in tbl_purchase_record.\n"
                            message += "server: " + str(serverId) + "\n"
                            message += "member: " + str(memberId) + "\n"
                            message += "role: " + str(roleId) + "\n"
                            message += "missing data."
                            raise Exception(message)

            oldRolePurchaseData = await conn.fetch('SELECT notes, amount_in FROM tbl_transactions WHERE server = $1 AND member = $2 AND (notes LIKE $3 OR notes LIKE $4)', serverId, memberId, TRANSACTION_BUY_ROLE + ": %(%)", TRANSACTION_REFUND_ROLE + ": %(%)")
            if oldRolePurchaseData is not None:
                oldUserRoles = dict()
                for row in oldRolePurchaseData:
                    note = row[0]
                    parsing = note.rpartition("(")
                    roleId = int(parsing[2][:len(parsing[2]) - 1])
                    amountIn = row[1]
                    if note.startswith(TRANSACTION_BUY_ROLE):
                        oldUserRoles[roleId] = -amountIn
                    elif note.startswith(TRANSACTION_REFUND_ROLE):
                        if oldUserRoles[roleId] != amountIn:
                            del oldUserRoles[roleId]
                        else:
                            message = "Integrity error in tbl_transactions.\n"
                            message += "server: " + str(serverId) + "\n"
                            message += "member: " + str(memberId) + "\n"
                            message += "purchase: " + str(oldUserRoles[roleId]) + "\n"
                            message += "refund: " + str(amountIn) + "\n"
                            message += "refunded incorrectly."
                            raise Exception(message)

                for roleId, oldCost in oldUserRoles.items():
                    newRolePurchaseData = await conn.fetchrow('SELECT amount_paid FROM tbl_purchase_record WHERE server = $1 AND member = $2 AND role = $3', serverId, memberId, roleId)
                    if newRolePurchaseData is None:
                        message = "Migration error in tbl_purchase_record.\n"
                        message += "server: " + str(serverId) + "\n"
                        message += "member: " + str(memberId) + "\n"
                        message += "role: " + str(roleId) + "\n"
                        message += "missing data."
                        raise Exception(message)
                    elif oldCost != newRolePurchaseData[0]:
                        message = "Migration error in tbl_purchase_record.\n"
                        message += "server: " + str(serverId) + "\n"
                        message += "member: " + str(memberId) + "\n"
                        message += "role: " + str(roleId) + "\n"
                        message += "old cost data: " + str(oldCost) + "\n"
                        message += "new cost data: " + str(newRolePurchaseData[0])
                        raise Exception(message)

        print("Transferring transaction record...")

        if not os.path.exists(TRANSACTION_DIRECTORY):
            os.mkdir(TRANSACTION_DIRECTORY)

        allTransactions = await conn.fetch('SELECT server, member, date, amount_in, notes FROM tbl_transactions')
        balanceRecord = dict()
        for row in allTransactions:
            serverId = row[0]
            memberId = row[1]
            date = row[2]
            amount_in = row[3]
            notes = row[4]
            if (serverId, memberId) not in balanceRecord:
                balanceRecord[serverId, memberId] = amount_in
            else:
                balanceRecord[serverId, memberId] += amount_in
            recordTransaction(serverId, memberId, date, amount_in, notes, balanceRecord[serverId, memberId])

        await conn.execute('DROP TABLE tbl_transactions')

        print("Migration Complete.")

    finally:
        await conn.close()

TRANSACTION_DIRECTORY = "TransactionRecords"

def recordTransaction(serverId, memberId, date, amount_in, notes, balance):
    filename = TRANSACTION_DIRECTORY + "/" + str(serverId) + "." + str(memberId) + ".csv"
    with open(filename, "a+", encoding='utf-8') as record:
        if record.tell() == 0:
            server = discord.utils.find(lambda s: s.id == serverId, discordConnection.guilds)
            member = discord.utils.find(lambda u: u.id == memberId, discordConnection.users)
            if server is None:
                serverName = "UNKNOWN SERVER"
            else:
                serverName = server.name
            if member is None:
                memberName = "UNKNOWN MEMBER"
            else:
                memberName = str(member)

            record.write("************************************************************************\n")
            record.write("*  TRANSACTION RECORD\n")
            record.write("*  SERVER: " + serverName + " (id: " + str(serverId) + ")\n")
            record.write("*  MEMBER: " + memberName + " (id: " + str(memberId) + ")\n")
            record.write("************************************************************************\n")
            record.write("date,amount in,notes,balance\n")
        record.write(date.isoformat() + "," + str(amount_in) + "," + notes + "," + str(balance) + "\n")

@discordConnection.event
async def on_ready():
    await migrate()
    await discordConnection.logout()

discordConnection.run(DISCORD_TOKEN)

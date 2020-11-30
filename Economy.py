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

import discord

import os

from Constants import *
from Utilities import *

PAYDAY_SETUP_COMMAND = "setuppayday"
PAYDAY_CLEAR_COMMAND = "clearpayday"
PAYDAY_COMMAND = "payday"
BALANCE_COMMAND = "balance"
BUY_ROLE_SETUP_COMMAND = "setuprole"
BUY_ROLE_REMOVE_COMMAND = "removerole"
LIST_ROLES_COMMAND = "rolemenu"
BUY_ROLE_COMMAND = "buyrole"
REFUND_ROLE_COMMAND = "refundrole"

TRANSACTION_PAYDAY = "Payday"
TRANSACTION_BUY_ROLE = "Buying Role"
TRANSACTION_REFUND_ROLE = "Refunding Role"
TRANSACTION_DIRECTORY = "TransactionRecords"

if not os.path.exists(TRANSACTION_DIRECTORY):
    os.mkdir(TRANSACTION_DIRECTORY)

def recordTransaction(server, member, date, amount_in, notes, balance):
    filename = TRANSACTION_DIRECTORY + "/" + str(server.id) + "." + str(member.id) + ".csv"
    with open(filename, "a+", encoding='utf-8') as record:
        if record.tell() == 0:
            record.write("************************************************************************\n")
            record.write("*  TRANSACTION RECORD\n")
            record.write("*  SERVER: " + server.name + " (id: " + str(server.id) + ")\n")
            record.write("*  MEMBER: " + str(member) + " (id: " + str(member.id) + ")\n")
            record.write("************************************************************************\n")
            record.write("date,amount in,notes,balance\n")
        record.write(date.isoformat() + "," + str(amount_in) + "," + notes + "," + str(balance) + "\n")

async def setupPayday(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_guild:
        parsing = commandArgs.partition(" ")
        amountString = parsing[0]
        parsing = parsing[2].rpartition(" ")
        currencyName = parsing[0]
        cooldownString = parsing[2]
        if amountString == "" or currencyName == "" or cooldownString == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with an amount of money to dole out, a currency name, and a cooldown time.")
        elif not amountString.isdigit():
            await message.channel.send("Please enter a number for the amount of money we're expected to dole out each payday.")
        else:
            amount = int(amountString)
            cooldown = parseTimeDelta(cooldownString)
            if cooldown is None:
                await message.channel.send("Cannot interpret what you entered for cooldown time. Please enter a number, followed by 'd', 'h', 'm', or 's', for day, hour, minute, or second.")
            else:
                conn = await getConnection()
                try:
                    serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_payday_settings WHERE server = $1', message.guild.id)
                    if serverData[0] > 0:
                        await conn.execute('UPDATE tbl_payday_settings SET amount = $1, cooldown = $2 WHERE server = $3', amount, cooldown, message.guild.id)
                        output = "Payday function successfully updated with the following parameters:\n"
                    else:
                        await conn.execute('INSERT INTO tbl_payday_settings (server, amount, cooldown) VALUES ($1, $2, $3)', message.guild.id, amount, cooldown)
                        output = "Payday function successfully set up with the following parameters:\n"
                    currencyData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_currency WHERE server = $1', message.guild.id)
                    if currencyData[0] > 0:
                        await conn.execute('UPDATE tbl_currency SET currency_name = $1 WHERE server = $2', currencyName, message.guild.id)
                    else:
                        await conn.execute('INSERT INTO tbl_currency (server, currency_name) VALUES ($1, $2)', message.guild.id, currencyName)
                    output += "We'll be giving out __" + amountString + "__ '__" + currencyName + "__' to any user who runs the payday command.\n"
                    output += "And after running the command they must wait __" + timeDeltaToString(cooldown) + "__ before running it again.\n"
                    await message.channel.send(output)
                finally:
                    await returnConnection(conn)

async def clearPayday(message):
    if message.author.permissions_in(message.channel).manage_guild:
        conn = await getConnection()
        try:
            serverData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_payday_settings WHERE server = $1', message.guild.id)
            if serverData[0] > 0:
                await conn.execute('DELETE FROM tbl_payday_settings WHERE server = $1', message.guild.id)
                await message.channel.send("Payday feature completely cleared out. If you want to reenable it, please run `" + getPrefix(message.guild) + PAYDAY_SETUP_COMMAND + "` again.")
            else:
                await message.channel.send("Payday feature has not even been set up, so there's no reason to clear it.")
        finally:
            await returnConnection(conn)

async def payday(message):
    conn = await getConnection()
    try:
        serverData = await conn.fetchrow('SELECT amount, cooldown FROM tbl_payday_settings WHERE server = $1', message.guild.id)
        currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
        if serverData is not None and currencyData is not None:
            paydayAmount = serverData[0]
            currencyName = currencyData[0]
            cooldown = serverData[1]
            accountData = await conn.fetchrow('SELECT balance, last_payday FROM tbl_account_balance WHERE server = $1 AND member = $2', message.guild.id, message.author.id)

            if accountData is None:
                currentFunds = 0
                lastPayday = None
            else:
                currentFunds = accountData[0]
                lastPayday = accountData[1]

            currentFunds += paydayAmount
            currentTime = message.created_at
            if lastPayday is None or lastPayday + cooldown < currentTime:
                recordTransaction(message.guild, message.author, currentTime, paydayAmount, TRANSACTION_PAYDAY, currentFunds)

                if accountData is None:
                    await conn.execute('INSERT INTO tbl_account_balance (server, member, balance, last_payday) VALUES ($1, $2, $3, $4)', message.guild.id, message.author.id, currentFunds, currentTime)
                    await message.channel.send("Welcome, " + message.author.mention + "! We've started you off with " + str(currentFunds) + " " + currencyName + " in your account.")
                else:
                    await conn.execute('UPDATE tbl_account_balance SET balance = $1, last_payday = $2 WHERE server = $3 AND member = $4', currentFunds, currentTime, message.guild.id, message.author.id)
                    await message.channel.send(message.author.mention + "! You now have " + str(currentFunds) + " " + currencyName + " in your account.")
            else:
                timeLeft = lastPayday + cooldown - currentTime
                await message.channel.send(message.author.mention + "! Please wait another " + timeDeltaToString(timeLeft) + " before attempting another payday.")
    finally:
        await returnConnection(conn)

async def balance(message):
    conn = await getConnection()
    try:
        currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
        if currencyData is not None:
            currencyName = currencyData[0]
            fundsData = await conn.fetchrow('SELECT balance FROM tbl_account_balance WHERE server = $1 AND member = $2', message.guild.id, message.author.id)

            if fundsData is None:
                currentFunds = 0
            else:
                currentFunds = fundsData[0]

            await message.channel.send(message.author.mention + "! You have " + str(currentFunds) + " " + currencyName + " in your account.")
    finally:
        await returnConnection(conn)

async def setupRole(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_roles:
        conn = await getConnection()
        try:
            currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
            if currencyData is not None:
                currencyName = currencyData[0]
                parsing = commandArgs.rpartition(" ")
                roleString = parsing[0]
                costString = parsing[2]
                if roleString == "" or costString == "":
                    await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with a role, and a cost.")
                elif not costString.isdigit():
                    await message.channel.send("Please enter a number for the cost of the role.")
                else:
                    role = parseRole(message.guild, roleString)
                    cost = int(costString)
                    if role is None:
                        await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
                    else:
                        roleCountData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = $1 AND role = $2', message.guild.id, role.id)
                        if roleCountData[0] > 0:
                            await conn.execute('UPDATE tbl_paid_roles SET cost = $1 WHERE server = $2 AND role = $3', cost, message.guild.id, role.id)
                            output = "Role '" + role.name + "' now set to cost " + costString + " " + currencyName + "."
                        else:
                            await conn.execute('INSERT INTO tbl_paid_roles (server, role, cost) VALUES ($1, $2, $3)', message.guild.id, role.id, cost)
                            output = "Role '" + role.name + "' now added to the menu, and costs " + costString + " " + currencyName + "."
                        await message.channel.send(output)
                        await persistBuyablesRole(role)
        finally:
            await returnConnection(conn)

async def removeRole(message, commandArgs):
    if message.author.permissions_in(message.channel).manage_roles:
        role = parseRole(message.guild, commandArgs)
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        else:
            conn = await getConnection()
            try:
                roleData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = $1 AND role = $2', message.guild.id, role.id)
                if roleData[0] > 0:
                    await conn.execute('DELETE FROM tbl_paid_roles WHERE server = $1 AND role = $2', message.guild.id, role.id)
                    await message.channel.send("'" + role.name + "' has been removed from the role menu.")
                else:
                    await message.channel.send("Can't find that role in the menu.")
            finally:
                await returnConnection(conn)

async def roleDeleted(role):
    conn = await getConnection()
    try:
        roleData = await conn.fetchrow('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = $1 AND role = $2', role.guild.id, role.id)
        if roleData[0] > 0:
            await conn.execute('DELETE FROM tbl_paid_roles WHERE server = $1 AND role = $2', role.guild.id, role.id)
    finally:
        await returnConnection(conn)

async def roleMenu(message):
    conn = await getConnection()
    try:
        currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
        allData = await conn.fetch('SELECT role, cost FROM tbl_paid_roles WHERE server = $1 ORDER BY cost', message.guild.id)
        if currencyData is not None and len(allData) > 0:
            output = "**Available Roles**\n"
            for roleData in allData:
                role = message.guild.get_role(roleData[0])
                if role is None:
                    await conn.execute('DELETE FROM tbl_paid_roles WHERE server = $1 AND role = $2', message.guild.id, roleData[0])
                else:
                    output += role.name + ": " + str(roleData[1]) + " " + currencyData[0] + "\n"
    finally:
        await returnConnection(conn)
    await message.channel.send(output)

async def buyRole(message, commandArgs):
    role = parseRole(message.guild, commandArgs)
    if role is None:
        await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
    elif message.author.roles.count(role) > 0:
        await message.channel.send("You already have this role.")
    else:
        conn = await getConnection()
        try:
            currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
            if currencyData is not None:
                currencyName = currencyData[0]
                costData = await conn.fetchrow('SELECT cost FROM tbl_paid_roles WHERE server = $1 AND role = $2', message.guild.id, role.id)
                accountData = await conn.fetchrow('SELECT balance FROM tbl_account_balance WHERE server = $1 AND member = $2', message.guild.id, message.author.id)
                purchaseData = await conn.fetchrow('SELECT amount_paid FROM tbl_purchase_record WHERE server = $1 AND member = $2 AND role = $3', message.guild.id, message.author.id, role.id)
                if costData is None:
                    await message.channel.send("Role not available for purchase.")
                elif purchaseData is not None:
                    await message.channel.send("You already bought this role.")
                elif accountData is None:
                    await message.channel.send("Can't find any account data. Please run the payday command (`" + getPrefix(message.guild) + PAYDAY_COMMAND + "`) at least once so we can give you some " + currencyName + ".")
                else:
                    roleCost = costData[0]
                    memberFunds = accountData[0]
                    if memberFunds < roleCost:
                        await message.channel.send("The '" + role.name + "' role costs " + str(roleCost) + " " + currencyName + ", and you only have " + str(memberFunds) + " " + currencyName + " in your account.")
                    else:
                        memberFunds -= roleCost
                        await conn.execute('INSERT INTO tbl_purchase_record (server, member, role, amount_paid) VALUES ($1, $2, $3, $4)', message.guild.id, message.author.id, role.id, roleCost)
                        await conn.execute('UPDATE tbl_account_balance SET balance = $1 WHERE server = $2 AND member = $3', memberFunds, message.guild.id, message.author.id)
                        recordTransaction(message.guild, message.author, message.created_at, -roleCost, TRANSACTION_BUY_ROLE + ": " + role.name + "(" + str(role.id) + ")", memberFunds)
                        await message.author.add_roles(role, reason="Purchased the role for " + str(roleCost) + " " + currencyName + ".")
                        await message.channel.send("Thank you for purchasing the '" + role.name + "' role for " + str(roleCost) + " " + currencyName + ". Your account balance is now: " + str(memberFunds) + " " + currencyName + ". Have a nice day.")
        finally:
            await returnConnection(conn)

async def refundRole(message, commandArgs):
    role = parseRole(message.guild, commandArgs)
    if role is None:
        await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
    elif message.author.roles.count(role) == 0:
        await message.channel.send("You don't have this role.")
    else:
        conn = await getConnection()
        try:
            currencyData = await conn.fetchrow('SELECT currency_name FROM tbl_currency WHERE server = $1', message.guild.id)
            if currencyData is not None:
                currencyName = currencyData[0]
                costData = await conn.fetchrow('SELECT amount_paid FROM tbl_purchase_record WHERE server = $1 AND member = $2 AND role = $3', message.guild.id, message.author.id, role.id)
                if costData is None:
                    await message.channel.send("Role cannot be refunded.")
                else:
                    roleCost = costData[0]
                    accountData = await conn.fetchrow('SELECT balance FROM tbl_account_balance WHERE server = $1 AND member = $2', message.guild.id, message.author.id)
                    if accountData is None:
                        memberFunds = roleCost
                    else:
                        memberFunds = accountData[0] + roleCost
                    recordTransaction(message.guild, message.author, message.created_at, roleCost, TRANSACTION_REFUND_ROLE + ": " + role.name + "(" + str(role.id) + ")", memberFunds)
                    await conn.execute('UPDATE tbl_account_balance SET balance = $1 WHERE server = $2 AND member = $3', memberFunds, message.guild.id, message.author.id)
                    await conn.execute('DELETE FROM tbl_purchase_record WHERE server = $1 AND member = $2 AND role = $3 AND amount_paid = $4', message.guild.id, message.author.id, role.id, roleCost)
                    await message.author.remove_roles(role, reason="Returned the role for " + str(roleCost) + " " + currencyName + ".")
                    await message.channel.send("You have returned the '" + role.name + "' role and " + str(roleCost) + " " + currencyName + " has been returned to you. Your account balance is now: " + str(memberFunds) + " " + currencyName + ". Have a nice day.")
        finally:
            await returnConnection(conn)

async def persistBuyablesMember(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = await getConnection()
        try:
            userData = await conn.fetch('SELECT role FROM tbl_purchase_record WHERE server = $1 AND member = $2', member.guild.id, member.id)
            userRoles = member.roles
            roleData = await conn.fetch('SELECT role FROM tbl_paid_roles WHERE server = $1', member.guild.id)
            paidRoles = []
        finally:
            await returnConnection(conn)
        for row in roleData:
            role = member.guild.get_role(row[0])
            if role is not None:
                paidRoles.append(role)
                if role in userRoles:
                    userRoles.remove(role)
        for row in userData:
            role = member.guild.get_role(row[0])
            if role in paidRoles:
                userRoles.append(role)
        userRoles.sort(key=lambda role: role.position)
        originalRoles = member.roles
        if len(originalRoles) == len(userRoles):
            isChange = False
            for i in range(len(originalRoles)):
                if originalRoles[i] != userRoles[i]:
                    isChange = True
                    break
        else:
            isChange = True
        if isChange:
            await member.edit(roles=userRoles, reason="Noticed some inconsistancies between the transaction records and the user's actual role assignment.")

async def persistBuyablesRole(role):
    conn = await getConnection()
    try:
        roleData = await conn.fetchrow('SELECT COUNT(cost) FROM tbl_paid_roles WHERE server = $1 AND role = $2', role.guild.id, role.id)
        if roleData[0] > 0:
            transactionData = await conn.fetch('SELECT member FROM tbl_purchase_record WHERE server = $1 AND role = $2', role.guild.id, role.id)
            await returnConnection(conn)
            paidMembers = []
            for row in transactionData:
                member = role.guild.get_member(row[0])
                if member is not None:
                    paidMembers.append(member)
            currentMembers = role.members
            paidMembers.sort(key=lambda member: member.id)
            currentMembers.sort(key=lambda member: member.id)
            if len(currentMembers) == len(paidMembers):
                isChange = False
                for i in range(len(currentMembers)):
                    if currentMembers[i] != paidMembers[i]:
                        isChange = True
                        break
            else:
                isChange = True
            if isChange:
                for paid in paidMembers:
                    if paid not in currentMembers:
                        await paid.add_roles(role, reason="Member paid for this role before, but doesn't currently have it.")
                for current in currentMembers:
                    if current not in paidMembers:
                        await current.remove_roles(role, reason="Member had this role, but didn't pay for it.")
    finally:
        await returnConnection(conn)

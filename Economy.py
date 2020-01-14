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

import datetime
import psycopg2

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

async def setupPayday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_SETUP_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].partition(" ")
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
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('SELECT COUNT(server) FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
                serverData = c.fetchone()
                if serverData[0] > 0:
                    c.execute('UPDATE tbl_payday_settings SET amount = %s, cooldown = %s WHERE server = %s', (amount, cooldown.total_seconds(), message.guild.id))
                    output = "Payday function successfully updated with the following parameters:\n"
                else:
                    c.execute('INSERT INTO tbl_payday_settings (server, amount, cooldown) VALUES (%s, %s, %s)', (message.guild.id, amount, cooldown.total_seconds()))
                    output = "Payday function successfully set up with the following parameters:\n"
                c.execute('SELECT COUNT(server) FROM tbl_currency WHERE server = %s', (message.guild.id,))
                currencyData = c.fetchone()
                if currencyData[0] > 0:
                    c.execute('UPDATE tbl_currency SET currency_name = %s WHERE server = %s', (currencyName, message.guild.id))
                else:
                    c.execute('INSERT INTO tbl_currency (server, currency_name) VALUES (%s, %s)', (message.guild.id, currencyName))
                output += "We'll be giving out __" + amountString + "__ '__" + currencyName + "__' to any user who runs the payday command.\n"
                output += "And after running the command they must wait __" + timeDeltaToString(cooldown) + "__ before running it again.\n"
                await message.channel.send(output)
                conn.commit()
                conn.close()

async def clearPayday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_CLEAR_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT COUNT(server) FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
        serverData = c.fetchone()
        if serverData[0] > 0:
            c.execute('DELETE FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
            await message.channel.send("Payday feature completely cleared out. If you want to reenable it, please run `" + COMMAND_PREFIX + PAYDAY_SETUP_COMMAND + "` again.")
            conn.commit()
        else:
            await message.channel.send("Payday feature has not even been set up, so there's no reason to clear it.")
        conn.close()

async def payday(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + PAYDAY_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT amount, cooldown FROM tbl_payday_settings WHERE server = %s', (message.guild.id,))
        serverData = c.fetchone()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        if serverData is not None and currencyData is not None:
            paydayAmount = serverData[0]
            currencyName = currencyData[0]
            cooldown = datetime.timedelta(seconds=serverData[1])
            c.execute('SELECT SUM(amount_in) FROM tbl_transactions WHERE server = %s AND member = %s', (message.guild.id, message.author.id))
            fundsData = c.fetchone()
            c.execute('SELECT MAX(date) FROM tbl_transactions WHERE server = %s AND member = %s AND notes = %s', (message.guild.id, message.author.id, TRANSACTION_PAYDAY))
            cooldownData = c.fetchone()

            if fundsData[0] is None:
                currentFunds = 0
            else:
                currentFunds = fundsData[0]

            if cooldownData[0] is None:
                lastPayday = None
            else:
                lastPayday = datetime.datetime.fromtimestamp(cooldownData[0])

            currentFunds += paydayAmount
            currentTime = message.created_at
            if lastPayday is None or lastPayday + cooldown < currentTime:
                c.execute('INSERT INTO tbl_transactions (date, server, member, amount_in, notes) VALUES (%s, %s, %s, %s, %s)', (message.created_at.timestamp(), message.guild.id, message.author.id, paydayAmount, TRANSACTION_PAYDAY))
                if lastPayday is None:
                    await message.channel.send("Welcome, " + message.author.mention + "! We've started you off with " + str(currentFunds) + " " + currencyName + " in your account.")
                else:
                    await message.channel.send(message.author.mention + "! You now have " + str(currentFunds) + " " + currencyName + " in your account.")
            else:
                timeLeft = lastPayday + cooldown - currentTime
                await message.channel.send(message.author.mention + "! Please wait another " + timeDeltaToString(timeLeft) + " before attempting another payday.")
            conn.commit()
        conn.close()

async def balance(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + BALANCE_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        if currencyData is not None:
            currencyName = currencyData[0]
            c.execute('SELECT SUM(amount_in) FROM tbl_transactions WHERE server = %s AND member = %s', (message.guild.id, message.author.id))
            fundsData = c.fetchone()

            if fundsData[0] is None:
                currentFunds = 0
            else:
                currentFunds = fundsData[0]

            await message.channel.send(message.author.mention + "! You have " + str(currentFunds) + " " + currencyName + " in your account.")
        conn.close()

async def setupRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + BUY_ROLE_SETUP_COMMAND and message.author.permissions_in(message.channel).manage_roles:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        if currencyData is not None:
            currencyName = currencyData[0]
            parsing = parsing[2].rpartition(" ")
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
                    c.execute('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
                    roleCountData = c.fetchone()
                    if roleCountData[0] > 0:
                        c.execute('UPDATE tbl_paid_roles SET cost = %s WHERE server = %s AND role = %s', (cost, message.guild.id, role.id))
                        output = "Role '" + role.name + "' now set to cost " + costString + " " + currencyName + "."
                    else:
                        c.execute('INSERT INTO tbl_paid_roles (server, role, cost) VALUES (%s, %s, %s)', (message.guild.id, role.id, cost))
                        output = "Role '" + role.name + "' now added to the menu, and costs " + costString + " " + currencyName + "."
                    await message.channel.send(output)
                    conn.commit()
                    await persistBuyablesRole(role)
        conn.close()

async def removeRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + BUY_ROLE_REMOVE_COMMAND and message.author.permissions_in(message.channel).manage_roles:
        role = parseRole(message.guild, parsing[2])
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        else:
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT COUNT(server) FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
            roleData = c.fetchone()
            if roleData[0] > 0:
                c.execute('DELETE FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
                await message.channel.send("'" + role.name + "' has been removed from the role menu.")
                conn.commit()
            else:
                await message.channel.send("Can't find that role in the menu.")
            conn.close()

async def roleMenu(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + LIST_ROLES_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
        currencyData = c.fetchone()
        c.execute('SELECT role, cost FROM tbl_paid_roles WHERE server = %s ORDER BY cost', (message.guild.id,))
        allData = c.fetchall()
        conn.close()
        if currencyData is not None and len(allData) > 0:
            output = "**Available Roles**\n"
            for roleData in allData:
                role = message.guild.get_role(roleData[0])
                output += role.name + ": " + str(roleData[1]) + " " + currencyData[0] + "\n"
        await message.channel.send(output)

async def buyRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + BUY_ROLE_COMMAND:
        role = parseRole(message.guild, parsing[2])
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        elif message.author.roles.count(role) > 0:
            await message.channel.send("You already have this role.")
        else:
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
            currencyData = c.fetchone()
            if currencyData is not None:
                currencyName = currencyData[0]
                c.execute('SELECT cost FROM tbl_paid_roles WHERE server = %s AND role = %s', (message.guild.id, role.id))
                costData = c.fetchone()
                c.execute('SELECT SUM(amount_in) FROM tbl_transactions WHERE server = %s AND member = %s', (message.guild.id, message.author.id))
                accountData = c.fetchone()
                if costData is None:
                    await message.channel.send("Role not available for purchase.")
                elif accountData[0] is None:
                    await message.channel.send("Can't find any account data. Please run the payday command (`" + COMMAND_PREFIX + PAYDAY_COMMAND + "`) at least once so we can give you some " + currencyName + ".")
                else:
                    roleCost = costData[0]
                    memberFunds = accountData[0]
                    if memberFunds < roleCost:
                        await message.channel.send("The '" + role.name + "' role costs " + str(roleCost) + " " + currencyName + ", and you only have " + str(memberFunds) + " " + currencyName + " in your account.")
                    else:
                        memberFunds -= roleCost
                        c.execute('INSERT INTO tbl_transactions (date, server, member, amount_in, notes) VALUES (%s, %s, %s, %s, %s)', (message.created_at.timestamp(), message.guild.id, message.author.id, -roleCost, TRANSACTION_BUY_ROLE + ": " + role.name + "(" + str(role.id) + ")"))
                        conn.commit()
                        await message.author.add_roles(role, reason="Purchased the role for " + str(roleCost) + " " + currencyName + ".")
                        await message.channel.send("Thank you for purchasing the '" + role.name + "' role for " + str(roleCost) + " " + currencyName + ". Your account balance is now: " + str(memberFunds) + " " + currencyName + ". Have a nice day.")
            conn.close()

async def refundRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + REFUND_ROLE_COMMAND:
        role = parseRole(message.guild, parsing[2])
        if role is None:
            await message.channel.send("You did not enter a valid role, please specify the role with either an `@` mention, the role's id number, or the role's full name.")
        elif message.author.roles.count(role) == 0:
            await message.channel.send("You don't have this role.")
        else:
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT currency_name FROM tbl_currency WHERE server = %s', (message.guild.id,))
            currencyData = c.fetchone()
            if currencyData is not None:
                currencyName = currencyData[0]
                c.execute('SELECT amount_in FROM tbl_transactions WHERE server = %s AND member = %s AND notes LIKE %s ORDER BY date DESC', (message.guild.id, message.author.id, TRANSACTION_BUY_ROLE + ": %(" + str(role.id) + ")"))
                costData = c.fetchone()
                if costData is None:
                    await message.channel.send("Role cannot be refunded.")
                else:
                    roleCost = -costData[0]
                    c.execute('SELECT SUM(amount_in) FROM tbl_transactions WHERE server = %s AND member = %s', (message.guild.id, message.author.id))
                    accountData = c.fetchone()
                    if accountData[0] is None:
                        memberFunds = roleCost
                    else:
                        memberFunds = accountData[0] + roleCost
                    c.execute('INSERT INTO tbl_transactions (date, server, member, amount_in, notes) VALUES (%s, %s, %s, %s, %s)', (message.created_at.timestamp(), message.guild.id, message.author.id, roleCost, TRANSACTION_REFUND_ROLE + ": " + role.name + "(" + str(role.id) + ")"))
                    conn.commit()
                    await message.author.remove_roles(role, reason="Returned the role for " + str(roleCost) + " " + currencyName + ".")
                    await message.channel.send("You have returned the '" + role.name + "' role and " + str(roleCost) + " " + currencyName + " has been returned to you. Your account balance is now: " + str(memberFunds) + " " + currencyName + ". Have a nice day.")
            conn.close()

async def persistBuyablesMember(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT notes FROM tbl_transactions WHERE server = %s AND member = %s AND (notes LIKE %s OR notes LIKE %s)', (member.guild.id, member.id, TRANSACTION_BUY_ROLE + ": %(%)", TRANSACTION_REFUND_ROLE + ": %(%)"))
        userData = c.fetchall()
        userRoles = member.roles
        c.execute('SELECT role FROM tbl_paid_roles WHERE server = %s', (member.guild.id,))
        roleData = c.fetchall()
        paidRoles = []
        for row in roleData:
            role = member.guild.get_role(row[0])
            paidRoles.append(role)
            if role in userRoles:
                userRoles.remove(role)
        for row in userData:
            note = row[0]
            parsing = note.rpartition("(")
            role = member.guild.get_role(int(parsing[2][:len(parsing[2]) - 1]))
            if role in paidRoles:
                if note.startswith(TRANSACTION_BUY_ROLE):
                    userRoles.append(role)
                elif note.startswith(TRANSACTION_REFUND_ROLE):
                    userRoles.remove(role)
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
        conn.close()

async def persistBuyablesRole(role):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT COUNT(cost) FROM tbl_paid_roles WHERE server = %s AND role = %s', (role.guild.id, role.id))
    roleData = c.fetchone()
    if roleData[0] > 0:
        c.execute('SELECT member, notes FROM tbl_transactions WHERE server = %s AND (notes LIKE %s OR notes LIKE %s) ORDER BY date', (role.guild.id, TRANSACTION_BUY_ROLE + ": %(" + str(role.id) + ")", TRANSACTION_REFUND_ROLE + ": %(" + str(role.id) + ")"))
        transactionData = c.fetchall()
        conn.close()
        paidMembers = []
        for row in transactionData:
            member = role.guild.get_member(row[0])
            note = row[1]
            if member is not None:
                if note.startswith(TRANSACTION_BUY_ROLE):
                    paidMembers.append(member)
                elif note.startswith(TRANSACTION_REFUND_ROLE):
                    paidMembers.remove(member)
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
    else:
        conn.close()

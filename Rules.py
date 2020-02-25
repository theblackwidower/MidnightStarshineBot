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

import asyncpg

from Constants import *
from Utilities import *

RULE_GET_COMMAND = "getrule"
RULE_SET_COMMAND = "setrule"
RULE_EDIT_COMMAND = "editrule"
RULE_DELETE_COMMAND = "deleterule"
RULE_GET_ALL_COMMAND = "getallrules"
RULE_GET_BACKUP_COMMAND = "getrulebackup"
RULE_CHANNEL_SET_COMMAND = "setrulechannel"
RULE_CHANNEL_CLEAR_COMMAND = "clearrulechannel"

async def setRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_SET_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        server_id = message.guild.id
        conn = await getConnection()
        await conn.execute('INSERT INTO tbl_rules (server, content) VALUES ($1, $2)', server_id, parsing[2])
        ruleData = await conn.fetchrow('SELECT COUNT(id) FROM tbl_rules WHERE server = $1', server_id)
        await message.channel.send("Rule #" + str(ruleData[0]) + " has been set to: " + parsing[2])
        await returnConnection(conn)
        await updateRuleChannel(message)

async def getRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_COMMAND:
        if parsing[2].isdigit():
            conn = await getConnection()
            ruleData = await conn.fetch('SELECT content FROM tbl_rules WHERE server = $1 ORDER BY id', message.guild.id)
            await returnConnection(conn)
            rule_num = int(parsing[2])
            if rule_num <= len(ruleData) and rule_num > 0:
                await message.channel.send("Rule #" + parsing[2] + ": " + ruleData[rule_num - 1][0])
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")


async def getRuleId(server_id, rule_num):
    conn = await getConnection()
    ruleData = await conn.fetch('SELECT id FROM tbl_rules WHERE server = $1 ORDER BY id', server_id)
    await returnConnection(conn)
    if rule_num <= len(ruleData) and rule_num > 0:
        returnValue = ruleData[rule_num - 1][0]
    else:
        returnValue = None
    return returnValue

async def editRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_EDIT_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].partition(" ")
        if parsing[0].isdigit():
            rule_id = await getRuleId(message.guild.id, int(parsing[0]))
            if rule_id is not None:
                conn = await getConnection()
                await conn.execute('UPDATE tbl_rules SET content = $1 WHERE id = $2', parsing[2], rule_id)
                await message.channel.send("Rule #" + parsing[0] + " is now: " + parsing[2])
                await returnConnection(conn)
                await updateRuleChannel(message)
            else:
                await message.channel.send("There is no rule #" + parsing[0])
        else:
            await message.channel.send("Please provide a valid number.")

async def deleteRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_DELETE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        if parsing[2].isdigit():
            rule_id = await getRuleId(message.guild.id, int(parsing[2]))
            if rule_id is not None:
                conn = await getConnection()
                await conn.execute('DELETE FROM tbl_rules WHERE id = $1', rule_id)
                await message.channel.send("Rule #" + parsing[2] + " has been deleted")
                await returnConnection(conn)
                await updateRuleChannel(message)
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")

async def getAllRules(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_ALL_COMMAND:
        conn = await getConnection()
        ruleData = await conn.fetch('SELECT content FROM tbl_rules WHERE server = $1 ORDER BY id', message.guild.id)
        await returnConnection(conn)
        count = len(ruleData)
        if count > 0:
            output = "**SERVER RULES** for " + message.guild.name + ":"
            for i in range(count):
                # TODO: add some kind of length control
                output += "\nRule #" + str(i + 1) + ": " + ruleData[i][0]
            await message.author.create_dm()
            await message.author.dm_channel.send(output)

            await message.channel.send(message.author.mention + "! A copy of the complete server rules have been sent to your DMs.")

async def getRuleBackup(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_BACKUP_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = await getConnection()
        ruleData = await conn.fetch('SELECT content FROM tbl_rules WHERE server = $1 ORDER BY id', message.guild.id)
        await returnConnection(conn)
        count = len(ruleData)
        if count > 0:
            output = "**BACKUP OF SERVER RULES** for " + message.guild.name + ": \n```"
            for i in range(count):
                # TODO: add some kind of length control
                output += "\n" + COMMAND_PREFIX + RULE_SET_COMMAND + " " + ruleData[i][0]
            output += "```"
            await message.author.create_dm()
            await message.author.dm_channel.send(output)

            await message.channel.send(message.author.mention + "! A backup of the complete server rules has been sent to your DMs.")

async def setRuleChannel(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_CHANNEL_SET_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        if parsing[2] == "":
            await message.channel.send("Please specify a rule channel.")
        elif len(message.channel_mentions) == 0:
            await message.channel.send("Please specify a valid rule channel.")
        else:
            ruleChannel = message.channel_mentions[0]
            server_id = message.guild.id
            conn = await getConnection()
            oldData = await conn.fetchrow('SELECT channel FROM tbl_rule_posting WHERE server = $1', server_id)
            if oldData is not None and oldData[0] == ruleChannel.id:
                await message.channel.send("The rules are already posted in that channel.")
            else:
                rulesData = await conn.fetch('SELECT content FROM tbl_rules WHERE server = $1 ORDER BY id', server_id)
                count = len(rulesData)
                ruleOutput = "**RULES:**"
                for i in range(count):
                    # TODO: add some kind of length control
                    ruleOutput += "\n\n" + str(i + 1) + ": " + rulesData[i][0]
                ruleMessage = await ruleChannel.send(ruleOutput)
                if oldData is None:
                    await conn.execute('INSERT INTO tbl_rule_posting (server, channel, message) VALUES ($1, $2, $3)', server_id, ruleChannel.id, ruleMessage.id)
                else:
                    await conn.execute('UPDATE tbl_rule_posting SET channel = $1, message = $2 WHERE server = $3', ruleChannel.id, ruleMessage.id, server_id)
                await message.channel.send("Rules now posted in " + ruleChannel.mention + ".")
            await returnConnection(conn)

async def clearRuleChannel(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_CHANNEL_CLEAR_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        server_id = message.guild.id
        conn = await getConnection()
        channelData = await conn.fetchrow('SELECT channel, message FROM tbl_rule_posting WHERE server = $1', server_id)
        if channelData is None:
            await message.channel.send("No rule postings recorded.")
        else:
            ruleChannel = message.guild.get_channel(channelData[0])
            try:
                ruleMessage = await ruleChannel.fetch_message(channelData[1])
                await ruleMessage.delete()
            except discord.errors.NotFound:
                pass
            await conn.execute('DELETE FROM tbl_rule_posting WHERE server = $1', server_id)
            await message.channel.send("Rule posting in " + ruleChannel.mention + " has been deleted.")
        await returnConnection(conn)

async def updateRuleChannel(message):
    server_id = message.guild.id
    conn = await getConnection()
    messageData = await conn.fetchrow('SELECT channel, message FROM tbl_rule_posting WHERE server = $1', server_id)
    if messageData is not None:
        try:
            ruleMessage = await message.guild.get_channel(messageData[0]).fetch_message(messageData[1])
            rulesData = await conn.fetch('SELECT content FROM tbl_rules WHERE server = $1 ORDER BY id', server_id)
            count = len(rulesData)
            ruleOutput = "**RULES:**"
            for i in range(count):
                # TODO: add some kind of length control
                ruleOutput += "\n\n" + str(i + 1) + ": " + rulesData[i][0]
            await ruleMessage.edit(content=ruleOutput)
        except discord.errors.NotFound:
            await message.channel.send("Error encountered updating rule posting. Post has likely been deleted.")
    await returnConnection(conn)

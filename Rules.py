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

import psycopg2

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
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('INSERT INTO tbl_rules (server, content) VALUES (%s, %s)', (server_id, parsing[2]))
        c.execute('SELECT COUNT(id) FROM tbl_rules WHERE server = %s', (server_id,))
        ruleData = c.fetchone()
        await message.channel.send("Rule #" + str(ruleData[0]) + " has been set to: " + parsing[2])
        conn.commit()
        conn.close()
        await updateRuleChannel(message)

async def getRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_COMMAND:
        if parsing[2].isdigit():
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (message.guild.id,))
            ruleData = c.fetchall()
            conn.close()
            rule_num = int(parsing[2])
            if rule_num <= len(ruleData) and rule_num > 0:
                await message.channel.send("Rule #" + parsing[2] + ": " + ruleData[rule_num - 1][0])
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")


def getRuleId(server_id, rule_num):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT id FROM tbl_rules WHERE server = %s ORDER BY id', (server_id,))
    ruleData = c.fetchall()
    conn.close()
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
            rule_id = getRuleId(message.guild.id, int(parsing[0]))
            if rule_id is not None:
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('UPDATE tbl_rules SET content = %s WHERE id = %s', (parsing[2], rule_id))
                await message.channel.send("Rule #" + parsing[0] + " is now: " + parsing[2])
                conn.commit()
                conn.close()
                await updateRuleChannel(message)
            else:
                await message.channel.send("There is no rule #" + parsing[0])
        else:
            await message.channel.send("Please provide a valid number.")

async def deleteRule(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_DELETE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        if parsing[2].isdigit():
            rule_id = getRuleId(message.guild.id, int(parsing[2]))
            if rule_id is not None:
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('DELETE FROM tbl_rules WHERE id = %s', (rule_id,))
                await message.channel.send("Rule #" + parsing[2] + " has been deleted")
                conn.commit()
                conn.close()
                await updateRuleChannel(message)
            else:
                await message.channel.send("There is no rule #" + parsing[2])
        else:
            await message.channel.send("Please provide a valid number.")

async def getAllRules(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_GET_ALL_COMMAND:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (message.guild.id,))
        ruleData = c.fetchall()
        conn.close()
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
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (message.guild.id,))
        ruleData = c.fetchall()
        conn.close()
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
            conn = psycopg2.connect(DATABASE_URL)
            c = conn.cursor()
            c.execute('SELECT channel FROM tbl_rule_posting WHERE server = %s', (server_id,))
            oldData = c.fetchone()
            if oldData is not None and oldData[0] == ruleChannel.id:
                await message.channel.send("The rules are already posted in that channel.")
            else:
                c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (server_id,))
                rulesData = c.fetchall()
                count = len(rulesData)
                ruleOutput = "**RULES:**"
                for i in range(count):
                    # TODO: add some kind of length control
                    ruleOutput += "\n\n" + str(i + 1) + ": " + rulesData[i][0]
                ruleMessage = await ruleChannel.send(ruleOutput)
                if oldData is None:
                    c.execute('INSERT INTO tbl_rule_posting (server, channel, message) VALUES (%s, %s, %s)', (server_id, ruleChannel.id, ruleMessage.id))
                else:
                    c.execute('UPDATE tbl_rule_posting SET channel = %s, message = %s WHERE server = %s', (ruleChannel.id, ruleMessage.id, server_id))
                await message.channel.send("Rules now posted in " + ruleChannel.mention + ".")
                conn.commit()
            conn.close()

async def clearRuleChannel(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + RULE_CHANNEL_CLEAR_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        server_id = message.guild.id
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT channel, message FROM tbl_rule_posting WHERE server = %s', (server_id,))
        channelData = c.fetchone()
        if channelData is None:
            await message.channel.send("No rule postings recorded.")
        else:
            ruleChannel = message.guild.get_channel(channelData[0])
            try:
                ruleMessage = await ruleChannel.fetch_message(channelData[1])
                await ruleMessage.delete()
            except discord.errors.NotFound:
                pass
            c.execute('DELETE FROM tbl_rule_posting WHERE server = %s', (server_id,))
            await message.channel.send("Rule posting in " + ruleChannel.mention + " has been deleted.")
            conn.commit()
        conn.close()

async def updateRuleChannel(message):
    server_id = message.guild.id
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('SELECT channel, message FROM tbl_rule_posting WHERE server = %s', (server_id,))
    messageData = c.fetchone()
    if messageData is not None:
        try:
            ruleMessage = await message.guild.get_channel(messageData[0]).fetch_message(messageData[1])
            c.execute('SELECT content FROM tbl_rules WHERE server = %s ORDER BY id', (server_id,))
            rulesData = c.fetchall()
            count = len(rulesData)
            ruleOutput = "**RULES:**"
            for i in range(count):
                # TODO: add some kind of length control
                ruleOutput += "\n\n" + str(i + 1) + ": " + rulesData[i][0]
            await ruleMessage.edit(content=ruleOutput)
        except discord.errors.NotFound:
            await message.channel.send("Error encountered updating rule posting. Post has likely been deleted.")
    conn.close()

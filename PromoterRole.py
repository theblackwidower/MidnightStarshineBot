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

SETUP_PROMOTER_ROLE_COMMAND = "setuppromoterrole"
CLEAR_PROMOTER_ROLE_COMMAND = "clearpromoterrole"

invitesCache = dict()

async def setupInviteDataCache(server):
    if server.id not in invitesCache:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = %s', (server.id,))
        serverData = c.fetchone()
        conn.close()
        if serverData[0] > 0:
            invitesCache[server.id] = await server.invites()

async def setupPromoterRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        parsing = parsing[2].rpartition(" ")
        recruitCountString = parsing[2]
        roleString = parsing[0]

        if roleString == "" or recruitCountString == "":
            await message.channel.send("I'm missing some information, I'm sure of it. You need to provide me with a role, and a number of recruits needed to qualify for the role.")
        else:
            role = parseRole(message.guild, roleString)
            if role is None:
                await message.channel.send("Cannot find the role entered.")
            elif not recruitCountString.isdigit():
                await message.channel.send("What you provided for number of recruits is not a number.")
            else:
                recruitCount = int(recruitCountString)
                conn = psycopg2.connect(DATABASE_URL)
                c = conn.cursor()
                c.execute('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = %s', (message.guild.id,))
                serverData = c.fetchone()
                if serverData[0] > 0:
                    c.execute('UPDATE tbl_promoter_role_settings SET role = %s, recruit_count = %s WHERE server = %s', (role.id, recruitCount, message.guild.id))
                    output = "Active user role successfully updated with the following parameters:\n"
                else:
                    c.execute('INSERT INTO tbl_promoter_role_settings (server, role, recruit_count) VALUES (%s, %s, %s)', (message.guild.id, role.id, recruitCount))
                    output = "Active user role successfully set up with the following parameters:\n"
                output += "We'll be assigning the \"__" + role.name + "__\" role...\n"
                output += "... to any user whose invites bring in __" + str(recruitCount) + "__ members.\n"
                await setupInviteDataCache(message.guild)
                await message.channel.send(output)
                conn.commit()
                conn.close()

async def clearPromoterRole(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + CLEAR_PROMOTER_ROLE_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT COUNT(server) FROM tbl_promoter_role_settings WHERE server = %s', (message.guild.id,))
        serverData = c.fetchone()
        if serverData[0] > 0:
            c.execute('DELETE FROM tbl_promoter_role_settings WHERE server = %s', (message.guild.id,))
            del invitesCache[message.guild.id]
            await message.channel.send("Promoter role feature completely cleared out. If you want to reenable it, please run `" + COMMAND_PREFIX + SETUP_PROMOTER_ROLE_COMMAND + "` again.")
            conn.commit()
        else:
            await message.channel.send("Promoter role feature has not even been set up, so there's no reason to clear it.")
        conn.close()

async def recordRecruit(recruit):
    if not recruit.bot:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT role, recruit_count FROM tbl_promoter_role_settings WHERE server = %s', (recruit.guild.id,))
        serverData = c.fetchone()
        if serverData is not None:
            role = recruit.guild.get_role(serverData[0])
            recruitCount = serverData[1]
            if recruit.guild.id not in invitesCache:
                await setupInviteDataCache(recruit.guild)
            else:
                foundInvite = None
                allInvites = await recruit.guild.invites()
                for invite in invitesCache[recruit.guild.id]:
                    updatedInvite = discord.utils.get(allInvites, id=invite.id)
                    if updatedInvite is not None and invite.uses < updatedInvite.uses:
                        foundInvite = updatedInvite
                        invitesCache[recruit.guild.id].remove(invite)
                        invitesCache[recruit.guild.id].append(updatedInvite)
                        break

                if foundInvite is None:
                    for invite in allInvites:
                        if invite not in invitesCache[recruit.guild.id]:
                            foundInvite = invite
                            invitesCache[recruit.guild.id].append(invite)
                            break

                if foundInvite is None:
                    raise Exception("Can't find invite of new user.")
                else:
                    recruiterId = foundInvite.inviter.id
                    if recruiterId != recruit.id:
                        c.execute('SELECT COUNT(recruiter) FROM tbl_recruitment_record WHERE server = %s AND recruited_member = %s', (recruit.guild.id, recruit.id))
                        repetitionData = c.fetchone()
                        if repetitionData[0] == 0:
                            c.execute('INSERT INTO tbl_recruitment_record (server, recruiter, recruited_member) VALUES (%s, %s, %s)', (recruit.guild.id, recruiterId, recruit.id))
                            conn.commit()
                            recruiter = recruit.guild.get_member(recruiterId)
                            if recruiter is not None and recruiter.roles.count(role) == 0:
                                c.execute('SELECT COUNT(recruited_member) FROM tbl_recruitment_record WHERE server = %s AND recruiter = %s', (recruit.guild.id, recruiter.id))
                                countData = c.fetchone()
                                if countData[0] >= recruitCount:
                                    await recruiter.add_roles(role, reason="Recruited a total of " + str(countData[0]) + " members.")
        conn.close()

async def persistPromoterRole(member):
    if isinstance(member, discord.Member) and not member.bot:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('SELECT role, recruit_count FROM tbl_promoter_role_settings WHERE server = %s', (member.guild.id,))
        serverData = c.fetchone()
        if serverData is not None:
            role = member.guild.get_role(serverData[0])
            minRecruitCount = serverData[1]
            c.execute('SELECT COUNT(recruited_member) FROM tbl_recruitment_record WHERE server = %s AND recruiter = %s', (member.guild.id, member.id))
            recordData = c.fetchone()
            recruitCount = recordData[0]
            if member.roles.count(role) > 0:
                if recruitCount < minRecruitCount:
                    await member.remove_roles(role, reason="This user does not qualify for the promoter role, as they have only recruited " + str(recruitCount) + " members out of the " + str(minRecruitCount) + " they need.")
            else:
                if recruitCount >= minRecruitCount:
                    await member.add_roles(role, reason="This user had their promoter role returned, since records show they recruited " + str(recruitCount) + " members, and they only need " + str(minRecruitCount) + " to qualify.")
        conn.close()

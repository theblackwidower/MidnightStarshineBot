import os

import discord
from dotenv import load_dotenv

import datetime

COMMAND_PREFIX = "ms!"

IS_EMOJI_CENSOR_ENABLED = True
IS_ECHO_ENABLED = True
IS_YAG_SNIPE_ENABLED = True

ECHO_USER = 204818040628576256

ECHO_COMMAND = "say"
ROLECALL_COMMAND = "rolecall"

YAG_ID = 204255221017214977

ACTIVE_ROLE = 635253363440877599

activeRecordLast = dict()
activeRecordStart = dict()

ACTIVE_GAP = datetime.timedelta(seconds=30)
ACTIVE_DURATION = datetime.timedelta(minutes=5)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Successfully connected to the following servers:')

    for guild in client.guilds:
        print(f'{guild.name}(id: {guild.id})')
        await yagSnipe(guild.get_member(YAG_ID))

@client.event
async def on_member_join(member):
    await yagSnipe(member)

@client.event
async def on_guild_join(server):
    await yagSnipe(server.get_member(YAG_ID))

@client.event
async def on_guild_role_update(before, after):
    await yagSnipe(after.guild.get_member(YAG_ID))

@client.event
async def on_message(message):
    await emoji_censor(message)
    if message.content.startswith(COMMAND_PREFIX):
        await echo(message)
        await rolecall(message)
    if not isActive(message.author):
        await checkActive(message)

@client.event
async def on_message_edit(old_message, message):
    await emoji_censor(message)

async def emoji_censor(message):
    if IS_EMOJI_CENSOR_ENABLED:
        content = message.content

        emojiCount = 0
        while True:
            # <:AnnoyedSweetieBelle:650749086105993218>
            customEmojiStart = content.find("<:")
            if customEmojiStart == -1:
                break
            customEmojiMid = content.find(":", customEmojiStart + 1)
            if customEmojiMid == -1:
                break
            customEmojiEnd = content.find(">", customEmojiMid + 1)
            if customEmojiEnd == -1:
                break

            # if content[customEmojiMid + 2:customEmojiEnd - 2].isdigit():
            content = content[0:customEmojiStart] + content[customEmojiEnd + 1:]
            emojiCount += 1

        # TODO: Detect Unicode emojis

        content = content.strip()
        messageLength = len(content)

        if (emojiCount > 0 and (messageLength < 3 or messageLength <= emojiCount)):
            await message.delete()

async def echo(message):
    if IS_ECHO_ENABLED:
        parsing = message.content.partition(" ")
        if parsing[0] == COMMAND_PREFIX + ECHO_COMMAND and message.author.id == ECHO_USER:
            await message.channel.send(parsing[2])
            await message.delete()

async def rolecall(message):
    parsing = message.content.partition(" ")
    if parsing[0] == COMMAND_PREFIX + ROLECALL_COMMAND and message.author.permissions_in(message.channel).manage_guild:
        content = parsing[2].strip()
        scannedRole = 0
        if len(content) > 0:
            for role in message.channel.guild.roles:
                if role.name == content:
                    scannedRole = role
                    break
            if scannedRole == 0:
                await message.channel.send("Invalid role name.")
                return
        users = 0
        if scannedRole == 0:
            users = message.channel.guild.members
        else:
            users = scannedRole.members

        index = [""]
        roles = message.channel.guild.roles
        for role in roles:
            index.append("")

        for user in users:
            if (user.nick is None):
                name = user.name
            else:
                name = user.nick + " (" + user.name + ")"
            index[user.top_role.position] += "   " + name + "\n"

        output = "**RoleCall**\n"
        for i in range(len(index) - 1, -1, -1):
            if len(index[i]) > 0:
                output += "*" + roles[i].name + "*:\n" + index[i] + "\n"

        await message.channel.send(output)

async def yagSnipe(member):
    if IS_YAG_SNIPE_ENABLED and member is not None and member.id == YAG_ID:
        permissions = member.guild.me.guild_permissions
        if member.top_role.position >= member.guild.me.top_role.position:
            print("Can't kick " + member.name + " in " + member.guild.name + ". Too low a role.")
        elif permissions.ban_members or permissions.administrator:
            await member.ban(reason="Being a shit bot.", delete_message_days=0)
        elif permissions.kick_members:
            await member.kick(reason="Being a shit bot.")
        else:
            print("Can't kick " + member.name + " in " + member.guild.name + ". Lacking permissions.")

def isActive(member):
    try:
        member.roles.index(member.guild.get_role(ACTIVE_ROLE))
        return True
    except ValueError:
        return False

async def checkActive(message):
    try:
        lastMessageTime = activeRecordLast[message.author.id]
        if message.created_at <= lastMessageTime + ACTIVE_GAP:
            startMessageTime = activeRecordStart[message.author.id]
            if message.created_at >= startMessageTime + ACTIVE_DURATION:
                await message.author.add_roles(message.guild.get_role(ACTIVE_ROLE))
        else:
            activeRecordStart[message.author.id] = message.created_at
    except KeyError:
        activeRecordStart[message.author.id] = message.created_at
    activeRecordLast[message.author.id] = message.created_at

client.run(token)

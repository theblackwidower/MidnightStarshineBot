import os

import discord
from dotenv import load_dotenv

import array

COMMAND_PREFIX = "ms!"

IS_EMOJI_CENSOR_ENABLED = True
IS_ECHO_ENABLED = True

ECHO_USER = 204818040628576256

ECHO_COMMAND = "say"
ROLECALL_COMMAND = "rolecall"

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Successfully connected to the following servers:')

    for guild in client.guilds:
        print(f'{guild.name}(id: {guild.id})')

@client.event
async def on_message(message):
    await emoji_censor(message)
    await echo(message)
    await rolecall(message)

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
        if message.content.startswith(COMMAND_PREFIX + ECHO_COMMAND + " ") and message.author.id == ECHO_USER:
            echo = message.content[len(COMMAND_PREFIX + ECHO_COMMAND + " "):]
            await message.channel.send(echo)
            await message.delete()

async def rolecall(message):
    if message.content.startswith(COMMAND_PREFIX + ROLECALL_COMMAND) and message.author.permissions_in(message.channel).manage_guild:
        content = message.content[len(COMMAND_PREFIX + ROLECALL_COMMAND):].strip()
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

client.run(token)

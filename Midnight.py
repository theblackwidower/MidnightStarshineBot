import os

import discord
from dotenv import load_dotenv

COMMAND_PREFIX = "ms!"

IS_EMOJI_CENSOR_ENABLED = True
IS_ECHO_ENABLED = True

ECHO_COMMAND = "say"

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
        if message.content.startswith(COMMAND_PREFIX + ECHO_COMMAND + " "):
            echo = message.content[len(COMMAND_PREFIX + ECHO_COMMAND + " "):]
            await message.channel.send(echo)
            await message.delete()

client.run(token)

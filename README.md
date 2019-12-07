# Midnight Starshine

This is Midnight Starshine, the Discord bot I built for Ponyworld.

This bot is planned to have many functions, all coded directly in the bot.

## Install

First of all, you'll need a Discord Bot Token. This is how the bot logs into Discord.

If you don't have a bot token, you can get one here: [Discord Developers Portal](https://discordapp.com/developers/applications)

With that, add a new file in the bot's root folder named `.env`. (The dot at the beginning is very important.)

This file should contain the following code:
```
DISCORD_TOKEN=[Insert Bot Token here]
```
Insert the token in the appropriate location. (Don't include the brackets.)

You'll need to install Python 3.7+.

You'll also need to install a few Python modules.
```
$ pip install -U discord.py
$ pip install -U python-dotenv
```

From here, running the bot is simple:
```
$ python Midnight.py
```

## Working Features

  * Stopping Emoji Spam
  * Echo feature (limited to access by a single user, me... can be customized)
  * Rolecall, lists all users (can be filtered by role) sorted by whatever their top role is.
  * YAG Snipe, automatically kicks or bans a specified user, designed to deal with problems related to the bot YAGPDB.xyz.

## Upcoming Features

  * On-the-fly rule lookup
  * Currency system ('payday' command)
  * Custom role assignment based on user activity rates
  * Time-delayed echo

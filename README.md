# Midnight Starshine

This is Midnight Starshine, the Discord bot I built for Ponyworld.

This bot is planned to have many functions, all coded directly in the bot.

## Install

First of all, you'll need a Discord Bot Token. This is how the bot logs into Discord.

With that, add a new file in the bot's root folder named `.env`. (The dot at the beginning is very important.)

This file should contain the following code:
```
DISCORD_TOKEN=[Insert Bot Token here]
```
Insert the token in the appropriate location. (Don't include the brackets.)

You'll need to install Python.

You'll also need to install a few Python modules.
```
$ pip install -U discord.py
$ pip install -U python-dotenv
```

From here, running the bot is simple:
```
$ python Midnight.py
```

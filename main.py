import asyncio
import discord
import logging
import os
from discord.ext import commands

# from discord_slash import SlashCommand
# Allows us to manage the command settings.
# from discord_slash.utils import manage_commands

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# intents = discord.Intents.default()
# intents.members = True
# intents.all()

# All intents can be found at https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents
intents = discord.Intents.all()
intents.members = True
intents.typing = False
intents.presences = False
intents.all()


bot = commands.Bot(command_prefix="!", intents=intents)


# @bot.command()
# async def load(ctx, extension):
#     bot.load_extension(f'cogs.{extension}')


# @bot.command()
# async def unload(ctx, extension):
#     bot.unload_extension(f'cogs.{extension}')


# @bot.command()
# async def reload(ctx, extension):
#     bot.unload_extension(f'cogs.{extension}')
#     bot.load_extension(f'cogs.{extension}')

# # for filename in os.listdir('./cogs'):
# #     if filename.endswith('.py'):
# #         bot.load_extension(f'cogs.{filename[:-3]}')

# async def load_extensions():
#     for filename in os.listdir("./cogs"):
#         if filename.endswith(".py"):
#             # -3 to cut off the .py from the file name
#             await bot.load_extension(f"cogs.{filename[:-3]}")


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f"cogs.{extension}")


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")


@bot.command()
async def reload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")
    bot.load_extension(f"cogs.{extension}")


@bot.command()
async def rename(ctx, name):
    await bot.user.edit(username=name)
    await ctx.message.delete()


async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # -3 to cut off the .py from the file name
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as err:
                print(f"couldn't load cogs.{filename[:-3]}. {err}")


# bot.run(os.getenv('TOKEN'))
async def main():
    await load_extensions()
    await bot.start(os.getenv("TOKEN"))


asyncio.run(main())

import asyncio
import discord
import logging
import os
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


# All intents can be found at https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents
intents = discord.Intents.all()
intents.members = True
intents.typing = False
intents.presences = False
intents.all()


bot = commands.Bot(command_prefix="!", intents=intents)


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
            cog_name = filename[:-3]  # remove the .py
            try:
                await bot.load_extension(f"cogs.{cog_name}")
            except Exception as err:
                print(f"couldn't load cogs.{cog_name}. {err}")


async def main():
    await load_extensions()
    await bot.start(os.getenv("TOKEN"))


asyncio.run(main())

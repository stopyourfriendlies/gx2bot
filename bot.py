import logging
from discord import Intents
from discord.ext import commands
from utils.logging_setup import new_logger
from config import get_cog_files

logger = new_logger("discord", logging.DEBUG)

# All intents can be found at https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents
intents = Intents.all()
intents.members = True
intents.typing = False
intents.presences = False
intents.all()


gxbot = commands.Bot(command_prefix="!", intents=intents)


# TODO: figure out actual command for these, probably add restrictions?
@gxbot.command()
async def load(ctx, extension):
    gxbot.load_extension(f"cogs.{extension}")


@gxbot.command()
async def unload(ctx, extension):
    gxbot.unload_extension(f"cogs.{extension}")


@gxbot.command()
async def reload(ctx, extension):
    gxbot.unload_extension(f"cogs.{extension}")
    gxbot.load_extension(f"cogs.{extension}")


@gxbot.command()
async def rename(ctx, name):
    await gxbot.user.edit(username=name)
    await ctx.message.delete()


async def load_extensions():
    for filename in get_cog_files():
        if filename.endswith(".py"):
            cog_name = filename[:-3]  # remove the .py
            try:
                await gxbot.load_extension(f"cogs.{cog_name}")
            except Exception as err:
                print(f"couldn't load cogs.{cog_name}. {err}")

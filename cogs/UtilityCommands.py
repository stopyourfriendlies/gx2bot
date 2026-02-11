from discord.ext import commands
import logging
from utils.logging_setup import new_logger

logger = new_logger("UtilityCommands", logging.INFO)


class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Utility Commands ready")
        logger.info("UtilityCommands Cog Loaded")

    # Type "!ping" to check if bot is online.
    @commands.command()
    async def ping(self, ctx):
        await ctx.message.author.send("pong")
        await ctx.message.delete()
        return


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))

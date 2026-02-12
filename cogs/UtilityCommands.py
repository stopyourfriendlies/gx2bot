from discord.ext import commands
from discord.utils import get
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

    # Type "!purge_role [role_name]" to delete all Members that have the specified Role.
    @commands.command()
    @commands.has_role("Admin")
    async def cmd_purge_role(self, ctx, role_name):
        await purge_role(self, ctx, role_name)
        await ctx.message.delete()

    # Type "!clear_channel [channel_name]" to delete all Messages within the specified channel.
    @commands.command()
    @commands.has_role("Admin")
    async def cmd_clear_channel(self, ctx, channel_name):
        await purge_channel(self, ctx, channel_name)
        await ctx.message.delete()


# TODO: Can these be merged with their wrapper commands?
# Type "!purge_role [role_name]" in a channel to remove all users from that role.
async def purge_role(self, ctx, role_name):
    logger.info(f"purge_role fired for {role_name} Role.")

    logger.info(f"grabbing role object")
    try:
        role = get(ctx.guild.roles, name=role_name)
    except:
        logger.error(f"failed to grab role object")
        return

    if role is None:
        logger.warning(f"{role_name} Role cannot be purged since it cannot be found.")
        return

    # Cycle through each member that has the Role and remove the Role.
    for member in role.members:
        logger.info(f"{role_name} Role removed from {member}.")
        await member.remove_roles(role)

    logger.info(f"purge_role finished. {role_name} purged of members.")
    return


# Type "!purge_channel [channel_name]" in a channel to remove all messages from that channel.
async def purge_channel(self, ctx, channel_name):
    logger.info(f"purge_channel fired for #{channel_name}.")

    logger.info(f"grabbing channel object")
    try:
        channel = get(self.bot.get_all_channels(), name=channel_name)
    except:
        logger.error(f"failed to grab channel object")
        return

    if channel is None:
        logger.error(f"channel object is None")
        return
    if channel.guild.name != ctx.guild.name:
        logger.error(
            f"Command was used in a guild that doesn't have the provided channel"
        )
        return
    # Purge messages from the Channel.
    logger.info(f"purging channel of messages")
    try:
        await channel.purge()
    except:
        logger.error(f"purging messages failed")
        return

    logger.info(f"#{channel_name} purged of messages.")
    return


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))

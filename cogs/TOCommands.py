from config import CREDENTIALS_FILENAME, SHEET_DISCORD_MEMBERS
from discord.ext import commands, tasks

import gspread

import logging
from utils.logging_setup import new_logger

logger = new_logger("TOCommands", logging.INFO)

gc = gspread.service_account(filename=CREDENTIALS_FILENAME)

gx2_discord_members_spreadsheet = gc.open(SHEET_DISCORD_MEMBERS)


### CLASS


class TOCommands(commands.Cog):

    ## Events

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("TO Commands ready")
        logger.info("TOCommands Cog loaded.")

    ## Commands

    # Type "!getMembersInRole [role_name]" to populate the specified Google Sheet with Members of that Role.
    # If you have a role_name with multiple words, surround it with quotes (example: '!getMembersInRole "CORE STAFF"')
    @commands.command()
    async def getMembersInRole(self, ctx, role_name):
        output = []
        for role in ctx.guild.roles:
            if role.name == role_name:
                # print(role.members)
                for member in role.members:
                    output.append(
                        [
                            str(member.id),
                            str(member.name),
                            str(member.discriminator),
                            str(member.nick),
                            member.bot,
                            str(member.guild.name),
                            str(member.guild.id),
                        ]
                    )

        # Sanity Check to make sure there are actually members that have the role before continuing.
        if len(output) <= 0:
            await ctx.message.delete()
            return

        try:
            # Grab the Google Sheet
            sheet = gx2_discord_members_spreadsheet.worksheet(role_name)
        except:
            # If the sheet doesn't exist for that role, create it
            sheet = gx2_discord_members_spreadsheet.add_worksheet(
                title=role_name, rows=100, cols=20
            )

            # Create header for the new sheet
            output.insert(
                0,
                [
                    "ID",
                    "Name",
                    "Discriminator",
                    "Nick",
                    "Bot?",
                    "Guild Name",
                    "Guild ID",
                    "Joined Names",
                ],
            )

        # Insert the Members into the Sheet
        sheet.append_rows(output)

        # Delete the message that was used to fire this command.
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(TOCommands(bot))

import discord
from discord.ext import commands, tasks

import gspread
from datetime import datetime, timezone
import re
from zoneinfo import ZoneInfo
import zoneinfo

# from pytz import timezone
import pytz

# from pytz import all_timezones
# import time
import asyncio
import os
import json
import requests
import threading
import queue
import time
import logging

# load environment variables from .env
from dotenv import load_dotenv

load_dotenv()


# set credentials to use on the google sheet
gc = gspread.service_account(filename="./credentials.json")

# Open a sheet from a spreadsheet in one go
scheduled_messages_sheet = gc.open(os.getenv("SHEET_SCHEDULED_MESSAGES"))


class ScheduledMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("Scheduled Messages ready")

    @tasks.loop(seconds=30.0)
    async def printer(self):
        print("CHECKING MESSAGES")
        messages = scheduled_messages_sheet.worksheet("Scheduler").get_all_values()
        # print(messages)
        # messages[1][2] = "OVERWRITE"

        test_index = messages[0].index("Test")
        status_index = messages[0].index("Status")
        date_index = messages[0].index("Date")
        time_index = messages[0].index("Time")
        category_index = messages[0].index("Category")
        channel_index = messages[0].index("Channel")
        channel_id_index = messages[0].index("Channel ID")
        message_index = messages[0].index("Message")
        embed_color_index = messages[0].index("Embed\nColor")
        embed_color_hex_index = messages[0].index("Embed\nColor Hex")
        embed_title_index = messages[0].index("Embed\nTitle")
        embed_description_index = messages[0].index("Embed\nDescription")
        embed_footer_index = messages[0].index("Embed\nFooter")
        embed_image_index = messages[0].index("Embed\nImage")
        embed_thumbnail_index = messages[0].index("Embed\nThumbnail")

        for i in range(1, len(messages)):
            if messages[i][status_index] == "SENT":
                continue

            if (
                messages[i][date_index] == ""
                or messages[i][time_index] == ""
                or messages[i][channel_id_index] == ""
            ):
                continue

            channel = self.bot.get_channel(int(messages[i][channel_id_index]))

            parsed_date_split = messages[i][date_index].split("/")
            parsed_month = parsed_date_split[0].zfill(2)
            parsed_day = parsed_date_split[1].zfill(2)
            parsed_year = parsed_date_split[2]
            # print(parsed_date_split)

            parsed_time_split = re.split(r"\W", messages[i][time_index])
            parsed_hour = parsed_time_split[0].zfill(2)
            parsed_minute = parsed_time_split[1].zfill(2)
            parsed_AMPM = parsed_time_split[2]
            # print(parsed_time_split)

            msgDateTime = (
                parsed_month
                + "/"
                + parsed_day
                + "/"
                + parsed_year
                + " "
                + parsed_hour
                + ":"
                + parsed_minute
                + " "
                + parsed_AMPM
            )
            # print(msgDateTime)
            msgDateTimeFormat = "%m/%d/%Y %I:%M %p"

            parsed_time = datetime.strptime(msgDateTime, msgDateTimeFormat)
            # parsed_time = datetime(int(parsed_year), int(parsed_month), int(parsed_day), int(parsed_hour), int(parsed_minute), 0, 0)

            # print(parsed_time.strftime(msgDateTimeFormat))

            tz = pytz.timezone("America/Los_Angeles")
            current_date = datetime.now(tz)

            # print(current_date.strftime(msgDateTimeFormat))
            # message[status_index] = "Valid"
            if parsed_time.strftime(msgDateTimeFormat) == current_date.strftime(
                msgDateTimeFormat
            ):
                print("match time")

                embed_var = discord.Embed()

                if (
                    messages[i][embed_color_hex_index] != ""
                    and messages[i][embed_title_index] != ""
                    and messages[i][embed_description_index] != ""
                ):
                    embed_var.title = messages[i][embed_title_index]
                    embed_var.description = messages[i][embed_description_index]
                    embed_var.color = int(messages[i][embed_color_hex_index], 0)

                    if messages[i][embed_footer_index] != "":
                        embed_var.set_footer(text=messages[i][embed_footer_index])

                    if messages[i][embed_image_index] != "":
                        embed_var.set_image(url=messages[i][embed_image_index])

                    if messages[i][embed_thumbnail_index] != "":
                        embed_var.set_thumbnail(url=messages[i][embed_thumbnail_index])

                    await channel.send(messages[i][message_index], embed=embed_var)
                    messages[i][status_index] = "SENT"
                    scheduled_messages_sheet.worksheet("Scheduler").update(
                        "B1:B" + str(len(messages)),
                        [sublist[1:2] for sublist in messages],
                    )
                    continue

                await channel.send(messages[i][message_index])
                messages[i][status_index] = "SENT"
                scheduled_messages_sheet.worksheet("Scheduler").update(
                    "B1:B" + str(len(messages)), [sublist[1:2] for sublist in messages]
                )
                continue

            # except:
            #     print('Error')
            #     message[status_index] == "Error"

        # # scheduled_messages_sheet.worksheet(
        #     "Scheduler").update(messages)

        # status_list = scheduled_messages_sheet.col_values(1)
        # time_list = scheduled_messages_sheet.col_values(2)
        # message_list = scheduled_messages_sheet.col_values(3)
        # channel_list = scheduled_messages_sheet.col_values(4)
        # color_list = scheduled_messages_sheet.col_values(5)
        # title_list = scheduled_messages_sheet.col_values(6)
        # description_list = scheduled_messages_sheet.col_values(7)
        # footer_list = scheduled_messages_sheet.col_values(8)
        # image_list = scheduled_messages_sheet.col_values(9)
        # thumbnail_list = scheduled_messages_sheet.col_values(10)
        # #print(self.index)
        # self.index += 1

        # for
        # current_time = time.localtime()
        # #print(time.strftime('%H:%M:%S',time.strptime(time_list[1], '%I:%M:%S %p')) + " =?= " + time.strftime('%H:%M:%S',current_time))
        # print(time.strftime('%H:%M',time.strptime(time_list[1], '%I:%M:%S %p')) + " =?= " + time.strftime('%H:%M',time.gmtime()))
        # #for time in time_list:
        # sheet_time = time.strftime('%H:%M',time.strptime(time_list[1], '%I:%M:%S %p'))
        # current_time = time.strftime('%H:%M',time.gmtime())
        # if sheet_time == current_time:
        #     print("YAY!")

    # Commands
    @commands.command()
    async def getChannels(self, ctx):
        # id_list = scheduled_messages_sheet.col_values(1)
        # username_list = subscribersSheet.col_values(2)
        # print(ctx.message.guild.text_channels)

        output = []

        for channel in ctx.message.guild.text_channels:
            print(channel.category)
            output.append(
                [
                    str(channel.guild.name),
                    str(channel.guild.id),
                    str(channel.position),
                    str(channel.category),
                    str(channel.category_id),
                    str(channel.name),
                    str(channel.id),
                    str(channel.type),
                    channel.topic,
                    channel.nsfw,
                ]
            )

            # scheduled_messages_sheet.worksheet("Channels").append_row(
            #     [str(channel.guild.id), str(channel.guild.name), str(channel.position), str(channel.category_id), str(channel.category), str(channel.id), str(channel.name), channel.nsfw, channel.topic, str(channel.type)])

        scheduled_messages_sheet.worksheet("Channels").append_rows(output)
        # if str(ctx.message.author.id) not in id_list:
        #     subscribersSheet.append_row([str(ctx.message.author.id), ctx.message.author.name, str(
        #         ctx.message.author.discriminator), 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.00])

        await ctx.message.delete()

    @commands.command()
    async def getRoles(self, ctx):
        # id_list = scheduled_messages_sheet.col_values(1)
        # username_list = subscribersSheet.col_values(2)
        # print(ctx.message.guild.text_channels)

        output = []

        for channel in ctx.message.guild.text_channels:
            print(channel.category)
            output.append(
                [
                    str(channel.guild.name),
                    str(channel.guild.id),
                    str(channel.position),
                    str(channel.category),
                    str(channel.category_id),
                    str(channel.name),
                    str(channel.id),
                    str(channel.type),
                    channel.topic,
                    channel.nsfw,
                ]
            )

            # scheduled_messages_sheet.worksheet("Channels").append_row(
            #     [str(channel.guild.id), str(channel.guild.name), str(channel.position), str(channel.category_id), str(channel.category), str(channel.id), str(channel.name), channel.nsfw, channel.topic, str(channel.type)])

        scheduled_messages_sheet.worksheet("Channels").append_rows(output)
        # if str(ctx.message.author.id) not in id_list:
        #     subscribersSheet.append_row([str(ctx.message.author.id), ctx.message.author.name, str(
        #         ctx.message.author.discriminator), 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.00])

        await ctx.message.delete()

    @commands.command()
    async def testScheduledMessages(self, ctx):
        messages = scheduled_messages_sheet.worksheet("Scheduler").get_all_values()

        print("Test Scheduled Messages Fired")

        test_index = messages[0].index("Test")
        status_index = messages[0].index("Status")
        date_index = messages[0].index("Date")
        time_index = messages[0].index("Time")
        category_index = messages[0].index("Category")
        channel_index = messages[0].index("Channel")
        channel_id_index = messages[0].index("Channel ID")
        message_index = messages[0].index("Message")
        embed_color_index = messages[0].index("Embed\nColor")
        embed_color_hex_index = messages[0].index("Embed\nColor Hex")
        embed_title_index = messages[0].index("Embed\nTitle")
        embed_description_index = messages[0].index("Embed\nDescription")
        embed_footer_index = messages[0].index("Embed\nFooter")
        embed_image_index = messages[0].index("Embed\nImage")
        embed_thumbnail_index = messages[0].index("Embed\nThumbnail")

        for i in range(1, len(messages)):
            if messages[i][status_index] == "SENT":
                continue

            if (
                messages[i][date_index] == ""
                or messages[i][time_index] == ""
                or messages[i][channel_id_index] == ""
            ):
                continue

            if str(messages[i][test_index]) == "TRUE":
                print("Test Requested")

                embed_var = discord.Embed()

                if (
                    messages[i][embed_color_hex_index] != ""
                    and messages[i][embed_title_index] != ""
                    and messages[i][embed_description_index] != ""
                ):
                    embed_var.title = messages[i][embed_title_index]
                    embed_var.description = messages[i][embed_description_index]
                    embed_var.color = int(messages[i][embed_color_hex_index], 0)

                    if messages[i][embed_footer_index] != "":
                        embed_var.set_footer(text=messages[i][embed_footer_index])

                    if messages[i][embed_image_index] != "":
                        embed_var.set_image(url=messages[i][embed_image_index])

                    if messages[i][embed_thumbnail_index] != "":
                        embed_var.set_thumbnail(url=messages[i][embed_thumbnail_index])

                    await ctx.send(messages[i][message_index], embed=embed_var)
                    messages[i][status_index] = "TESTED"
                    scheduled_messages_sheet.worksheet("Scheduler").update(
                        "B1:B" + str(len(messages)),
                        [sublist[1:2] for sublist in messages],
                    )
                    continue

                await ctx.send(messages[i][message_index])
                messages[i][status_index] = "TESTED"
                scheduled_messages_sheet.worksheet("Scheduler").update(
                    "B1:B" + str(len(messages)), [sublist[1:2] for sublist in messages]
                )
                continue

            # except:
            #     print('Error')
            #     message[status_index] == "Error"
        await ctx.message.delete()


# def setup(bot):
#     bot.add_cog(ScheduledMessages(bot))


async def setup(bot):
    await bot.add_cog(ScheduledMessages(bot))

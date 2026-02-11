import asyncio
from dotenv import load_dotenv
from bot import gxbot, load_extensions
from config import DISCORD_TOKEN

load_dotenv()


async def main():
    await load_extensions()
    await gxbot.start(DISCORD_TOKEN)


asyncio.run(main())

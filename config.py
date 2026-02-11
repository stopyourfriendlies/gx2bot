import os

DISCORD_TOKEN = os.getenv("TOKEN", "")
assert DISCORD_TOKEN != "", "MISSING DISCORD_TOKEN"


# Function, not a constant. Needs to evaluate at run-time.
def get_cog_files():
    return os.listdir("./cogs")

import os
import asyncio
import logging

import discord
from discord.ext import commands

from db.database import init_db
from bot.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("main")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (id={bot.user.id})")
    await bot.tree.sync()
    logger.info("Slash commands synced.")
    setup_scheduler(bot)


async def main():
    init_db()
    async with bot:
        await bot.load_extension("bot.cogs.toggle")
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

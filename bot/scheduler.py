"""
APScheduler 기반 발송 스케줄러.

- 영어: 매주 월/목 오전 9시
- 일본어: 매일 오전 10시

각 작업은 길드 설정의 enabled 플래그를 먼저 확인하고,
꺼져 있으면 아무것도 하지 않고 조용히 반환한다(스킵).
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db.database import SessionLocal
from db.models import GuildSettings
from bot.content import get_next_english_situation, get_next_japanese_sentence
from bot.formatting import format_english_embed, format_japanese_embed

logger = logging.getLogger("scheduler")


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    scheduler.add_job(
        send_english_to_all_guilds,
        trigger=CronTrigger(day_of_week="mon,thu", hour=9, minute=0),
        args=[bot],
        id="english_shadowing",
        replace_existing=True,
    )

    scheduler.add_job(
        send_japanese_to_all_guilds,
        trigger=CronTrigger(hour=10, minute=0),
        args=[bot],
        id="japanese_sentence",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started: english(mon,thu 09:00), japanese(daily 10:00)")
    return scheduler


async def send_english_to_all_guilds(bot):
    db = SessionLocal()
    try:
        settings_list = db.query(GuildSettings).filter(GuildSettings.english_enabled.is_(True)).all()
        if not settings_list:
            return

        situation = await get_next_english_situation(db)
        if situation is None:
            logger.warning("English situation pool is empty.")
            return

        embed = format_english_embed(situation)
        for settings in settings_list:
            await _send_embed_to_guild(bot, settings, embed)
    finally:
        db.close()


async def send_japanese_to_all_guilds(bot):
    db = SessionLocal()
    try:
        settings_list = db.query(GuildSettings).filter(GuildSettings.japanese_enabled.is_(True)).all()
        if not settings_list:
            return

        sentence = await get_next_japanese_sentence(db)
        if sentence is None:
            logger.warning("Japanese sentence pool is empty.")
            return

        embed = format_japanese_embed(sentence)
        for settings in settings_list:
            await _send_embed_to_guild(bot, settings, embed)
    finally:
        db.close()


async def _send_embed_to_guild(bot, settings: GuildSettings, embed):
    guild = bot.get_guild(settings.guild_id)
    if guild is None:
        logger.warning(f"Guild {settings.guild_id} not found (bot not in server?).")
        return

    channel = None
    if settings.channel_id:
        channel = guild.get_channel(settings.channel_id)

    if channel is None:
        # 채널 미설정 시 텍스트 채널 중 첫 번째에 발송
        channel = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

    if channel is None:
        logger.warning(f"No sendable channel found in guild {guild.id}.")
        return

    await channel.send(embed=embed)

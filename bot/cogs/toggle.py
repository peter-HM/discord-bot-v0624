"""슬래시 명령어: /english on|off, /japanese on|off, /setchannel, /shadow_now"""

import discord
from discord import app_commands
from discord.ext import commands

from db.database import SessionLocal
from db.models import GuildSettings
from bot.content import get_next_english_situation, get_next_japanese_sentence
from bot.formatting import format_english_embed, format_japanese_embed


def _get_or_create_settings(db, guild_id: int) -> GuildSettings:
    settings = db.query(GuildSettings).filter(GuildSettings.guild_id == guild_id).first()
    if settings is None:
        settings = GuildSettings(guild_id=guild_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


class ToggleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="english", description="영어 섀도잉 자동 발송 on/off (월,목 09:00)")
    @app_commands.describe(state="on 또는 off")
    @app_commands.choices(state=[
        app_commands.Choice(name="on", value="on"),
        app_commands.Choice(name="off", value="off"),
    ])
    async def english(self, interaction: discord.Interaction, state: app_commands.Choice[str]):
        db = SessionLocal()
        try:
            settings = _get_or_create_settings(db, interaction.guild_id)
            settings.english_enabled = state.value == "on"
            db.commit()
            await interaction.response.send_message(
                f"영어 섀도잉 발송이 **{'켜짐' if settings.english_enabled else '꺼짐'}** 상태로 설정되었습니다.",
                ephemeral=True,
            )
        finally:
            db.close()

    @app_commands.command(name="japanese", description="일본어 한 문장 자동 발송 on/off (매일 10:00)")
    @app_commands.describe(state="on 또는 off")
    @app_commands.choices(state=[
        app_commands.Choice(name="on", value="on"),
        app_commands.Choice(name="off", value="off"),
    ])
    async def japanese(self, interaction: discord.Interaction, state: app_commands.Choice[str]):
        db = SessionLocal()
        try:
            settings = _get_or_create_settings(db, interaction.guild_id)
            settings.japanese_enabled = state.value == "on"
            db.commit()
            await interaction.response.send_message(
                f"일본어 문장 발송이 **{'켜짐' if settings.japanese_enabled else '꺼짐'}** 상태로 설정되었습니다.",
                ephemeral=True,
            )
        finally:
            db.close()

    @app_commands.command(name="setchannel", description="발송 채널을 현재 채널로 지정")
    async def setchannel(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            settings = _get_or_create_settings(db, interaction.guild_id)
            settings.channel_id = interaction.channel_id
            db.commit()
            await interaction.response.send_message(
                f"발송 채널이 <#{interaction.channel_id}> 로 설정되었습니다.", ephemeral=True
            )
        finally:
            db.close()

    @app_commands.command(name="shadow_now", description="테스트용: 영어 시나리오를 즉시 1개 발송")
    async def shadow_now(self, interaction: discord.Interaction):
        await interaction.response.defer()  # LLM 생성이 몇 초 걸릴 수 있어 응답을 미룸
        db = SessionLocal()
        try:
            situation = await get_next_english_situation(db)
            if situation is None:
                await interaction.followup.send("등록된 영어 시나리오가 없습니다.")
                return
            embed = format_english_embed(situation)
            await interaction.followup.send(embed=embed)
        finally:
            db.close()

    @app_commands.command(name="japanese_now", description="테스트용: 일본어 문장을 즉시 1개 발송")
    async def japanese_now(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = SessionLocal()
        try:
            sentence = await get_next_japanese_sentence(db)
            if sentence is None:
                await interaction.followup.send("등록된 일본어 문장이 없습니다.")
                return
            embed = format_japanese_embed(sentence)
            await interaction.followup.send(embed=embed)
        finally:
            db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(ToggleCog(bot))

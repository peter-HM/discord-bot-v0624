"""Discord embed/메시지 포맷팅 헬퍼."""

import discord


def format_english_embed(situation) -> discord.Embed:
    """영어 섀도잉 시나리오를 Discord embed로 변환.

    대화 본문은 그대로 보여주고, 표현 노트는 스포일러(||...||)로 가려서
    먼저 듣고 추측한 뒤 확인하는 흐름을 유도한다.
    """
    embed = discord.Embed(
        title=f"English shadowing: {situation.title}",
        color=discord.Color.blue(),
    )

    dialogue_lines = "\n".join(
        f"**{turn['speaker']}**: {turn['line']}" for turn in situation.dialogue
    )
    embed.add_field(name="Dialogue", value=dialogue_lines, inline=False)

    if situation.expressions:
        notes = "\n".join(
            f"- `{e['phrase']}` : {e['meaning']}" for e in situation.expressions
        )
        embed.add_field(name="Expression notes (spoiler)", value=f"||{notes}||", inline=False)

    embed.set_footer(text="Read it out loud, then shadow the audio in your head.")
    return embed


def format_japanese_embed(sentence) -> discord.Embed:
    """일본어 초급 문장을 Discord embed로 변환."""
    embed = discord.Embed(
        title="今日の一文 (오늘의 한 문장)",
        color=discord.Color.red(),
    )
    embed.add_field(name="文章", value=sentence.sentence, inline=False)
    if sentence.furigana:
        embed.add_field(name="ふりがな", value=sentence.furigana, inline=False)
    if sentence.romaji:
        embed.add_field(name="Romaji", value=sentence.romaji, inline=False)
    embed.add_field(name="뜻", value=sentence.translation, inline=False)
    return embed

"""
초기 시드 데이터 삽입 스크립트.

사용법:
    docker compose exec bot python -m seed.seed_data

이미 데이터가 있으면 건너뛴다(중복 삽입 방지).
"""

from db.database import SessionLocal, init_db
from db.models import EnglishSituation, JapaneseSentence

ENGLISH_SITUATIONS = [
    {
        "title": "동료가 휴가 가서 일이 몰릴 때",
        "dialogue": [
            {"speaker": "A", "line": "Hey, I heard Mark's out this week. You good?"},
            {"speaker": "B", "line": "Honestly, I'm swamped. Might have to pull an all-nighter."},
            {"speaker": "A", "line": "Yikes. Wanna loop in Sarah? She's pretty free right now."},
            {"speaker": "B", "line": "Yeah, let's touch base with her after lunch."},
        ],
        "expressions": [
            {"phrase": "swamped", "meaning": "일이 너무 많아 바쁜"},
            {"phrase": "pull an all-nighter", "meaning": "밤새서 일하다"},
            {"phrase": "loop someone in", "meaning": "~를 논의에 끼워 넣다"},
            {"phrase": "touch base", "meaning": "짧게 상황을 공유하다"},
        ],
    },
    {
        "title": "갑자기 잡힌 회의에 대한 불만",
        "dialogue": [
            {"speaker": "A", "line": "Did you see the calendar invite? Another meeting got slapped on top."},
            {"speaker": "B", "line": "Ugh, my schedule's already packed. Can we push it?"},
            {"speaker": "A", "line": "I'll ping the organizer and see if we can reschedule."},
            {"speaker": "B", "line": "Thanks, I owe you one."},
        ],
        "expressions": [
            {"phrase": "slap something on", "meaning": "갑자기/막무가내로 끼워넣다"},
            {"phrase": "packed schedule", "meaning": "일정이 빡빡한"},
            {"phrase": "ping someone", "meaning": "(메신저 등으로) 짧게 연락하다"},
            {"phrase": "I owe you one", "meaning": "신세 좀 졌다"},
        ],
    },
    {
        "title": "프로젝트 마감 직전 상황 공유",
        "dialogue": [
            {"speaker": "A", "line": "Where are we on the launch? Crunch time's starting to hit."},
            {"speaker": "B", "line": "We're cutting it close, but I think we'll make it."},
            {"speaker": "C", "line": "Let's not jinx it. I'll circle back once QA wraps up."},
            {"speaker": "A", "line": "Sounds good, keep me in the loop."},
        ],
        "expressions": [
            {"phrase": "crunch time", "meaning": "마감 직전 바쁜 시기"},
            {"phrase": "cut it close", "meaning": "시간이 빠듯하다"},
            {"phrase": "circle back", "meaning": "나중에 다시 알려주다/논의하다"},
            {"phrase": "keep someone in the loop", "meaning": "계속 정보를 공유해주다"},
        ],
    },
    {
        "title": "신입에게 업무 인수인계",
        "dialogue": [
            {"speaker": "A", "line": "So this is the part where it gets a bit messy, just a heads up."},
            {"speaker": "B", "line": "Got it. Should I just wing it if something breaks?"},
            {"speaker": "A", "line": "Nah, just shoot me a message and I'll walk you through it."},
            {"speaker": "B", "line": "Cool, appreciate it."},
        ],
        "expressions": [
            {"phrase": "heads up", "meaning": "미리 알려주는 말, 주의 환기"},
            {"phrase": "wing it", "meaning": "준비 없이 즉흥적으로 하다"},
            {"phrase": "shoot someone a message", "meaning": "메시지를 짧게 보내다"},
            {"phrase": "walk someone through", "meaning": "차근차근 설명해주다"},
        ],
    },
    {
        "title": "회의 중 의견이 갈릴 때",
        "dialogue": [
            {"speaker": "A", "line": "I'm not sold on this approach, to be honest."},
            {"speaker": "B", "line": "Fair enough, what's bugging you about it?"},
            {"speaker": "A", "line": "It just feels like we're putting the cart before the horse."},
            {"speaker": "B", "line": "Hmm, let's table this and revisit after the data comes in."},
        ],
        "expressions": [
            {"phrase": "not sold on something", "meaning": "확신이 들지 않는"},
            {"phrase": "bug someone", "meaning": "신경 쓰이게 하다"},
            {"phrase": "put the cart before the horse", "meaning": "순서가 뒤바뀐 일을 하다"},
            {"phrase": "table something", "meaning": "논의를 잠시 미루다"},
        ],
    },
    {
        "title": "퇴근 후 동료와 가벼운 잡담",
        "dialogue": [
            {"speaker": "A", "line": "Long day, huh? You heading out?"},
            {"speaker": "B", "line": "Yeah, I'm beat. Gonna call it a day."},
            {"speaker": "A", "line": "Same. Let's grab a coffee tomorrow and catch up."},
            {"speaker": "B", "line": "Sounds like a plan."},
        ],
        "expressions": [
            {"phrase": "I'm beat", "meaning": "너무 피곤하다"},
            {"phrase": "call it a day", "meaning": "오늘 일은 여기까지 하다"},
            {"phrase": "catch up", "meaning": "근황을 나누다"},
            {"phrase": "sounds like a plan", "meaning": "그렇게 하자, 좋은 생각이다"},
        ],
    },
]

JAPANESE_SENTENCES = [
    {
        "sentence": "今日は天気がいいですね。",
        "furigana": "きょうはてんきがいいですね。",
        "romaji": "Kyō wa tenki ga ii desu ne.",
        "translation": "오늘은 날씨가 좋네요.",
    },
    {
        "sentence": "お疲れ様でした。",
        "furigana": "おつかれさまでした。",
        "romaji": "Otsukaresama deshita.",
        "translation": "수고하셨습니다.",
    },
    {
        "sentence": "ちょっと待ってください。",
        "furigana": "ちょっとまってください。",
        "romaji": "Chotto matte kudasai.",
        "translation": "잠깐 기다려 주세요.",
    },
    {
        "sentence": "これはいくらですか。",
        "furigana": "これはいくらですか。",
        "romaji": "Kore wa ikura desu ka.",
        "translation": "이거 얼마예요?",
    },
    {
        "sentence": "また後で連絡します。",
        "furigana": "またあとでれんらくします。",
        "romaji": "Mata ato de renraku shimasu.",
        "translation": "나중에 다시 연락할게요.",
    },
    {
        "sentence": "すみません、これは何ですか。",
        "furigana": "すみません、これはなんですか。",
        "romaji": "Sumimasen, kore wa nan desu ka.",
        "translation": "저기요, 이건 뭐예요?",
    },
    {
        "sentence": "今日はとても忙しいです。",
        "furigana": "きょうはとてもいそがしいです。",
        "romaji": "Kyō wa totemo isogashii desu.",
        "translation": "오늘은 아주 바빠요.",
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        if db.query(EnglishSituation).count() == 0:
            for item in ENGLISH_SITUATIONS:
                db.add(EnglishSituation(**item))
            print(f"Inserted {len(ENGLISH_SITUATIONS)} English situations.")
        else:
            print("English situations already exist, skipping.")

        if db.query(JapaneseSentence).count() == 0:
            for item in JAPANESE_SENTENCES:
                db.add(JapaneseSentence(**item))
            print(f"Inserted {len(JAPANESE_SENTENCES)} Japanese sentences.")
        else:
            print("Japanese sentences already exist, skipping.")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()

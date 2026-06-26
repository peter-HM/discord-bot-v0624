# discord-bot-v0624

외국계 기업 취업 준비를 위한 영어/일본어 학습 Discord 봇.

- 영어: 매주 월/목 오전 9시, 실무 구어체 표현 중심 2~3인 대화 시나리오 발송
- 일본어: 매일 오전 10시, 초급 회화 문장 1개 발송 (후리가나/로마자/번역 포함)

## 기술 스택

- Python 3.11, discord.py 2.4
- SQLAlchemy + PostgreSQL
- APScheduler (cron 트리거)
- Docker / Docker Compose
- GitHub Actions (집 서버 SSH 배포)

## 빠른 시작

1. Discord 봇 생성
   - https://discord.com/developers/applications 에서 New Application 생성
   - Bot 탭에서 토큰 발급, MESSAGE CONTENT 등 필요한 Privileged Intents는 현재 구조상 불필요 (슬래시 명령어만 사용)
   - OAuth2 > URL Generator에서 `bot`, `applications.commands` 스코프 체크 후 초대 링크로 서버에 추가

2. 환경변수 설정

   ```bash
   cp .env.example .env
   # .env 파일에 DISCORD_TOKEN, POSTGRES_PASSWORD 입력
   ```

3. 실행

   ```bash
   docker compose up -d --build
   docker compose exec bot python -m seed.seed_data   # 최초 1회, 초기 콘텐츠 삽입
   ```

4. Discord에서 확인

   - `/setchannel` : 현재 채널을 발송 채널로 지정
   - `/english on` : 영어 섀도잉 발송 켜기
   - `/japanese on` : 일본어 문장 발송 켜기
   - `/shadow_now`, `/japanese_now` : 테스트용 즉시 발송

## 폴더 구조

```
discord-bot-v0624/
├── bot/
│   ├── cogs/toggle.py    # 슬래시 명령어
│   ├── content.py        # 콘텐츠 선택 로직 (추후 LLM 전환 지점)
│   ├── formatting.py     # Discord embed 포맷팅
│   ├── scheduler.py      # APScheduler 발송 트리거
│   └── main.py           # 엔트리포인트
├── db/
│   ├── database.py       # SQLAlchemy 연결
│   └── models.py         # GuildSettings, EnglishSituation, JapaneseSentence
├── seed/
│   └── seed_data.py      # 초기 시드 데이터
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/deploy.yml
```

## CI/CD (GitHub Actions)

`main` 브랜치에 push하면 집 서버에 SSH로 접속해 `git pull` 후 `docker compose up -d --build`를 실행합니다.

GitHub repo Settings > Secrets and variables > Actions 에 다음을 등록하세요:

| Secret | 설명 |
|---|---|
| `HOME_SERVER_HOST` | 집 서버 접속 주소 (도메인 또는 동적 DNS) |
| `HOME_SERVER_USER` | SSH 사용자명 |
| `HOME_SERVER_SSH_KEY` | SSH 프라이빗 키 |
| `HOME_SERVER_SSH_PORT` | SSH 포트 |
| `HOME_SERVER_PROJECT_PATH` | 서버 내 프로젝트 경로 |

> 집 네트워크가 동적 IP라면 DDNS(예: DuckDNS, No-IP) 설정이 필요합니다. Discord 봇 자체는 outbound 연결만 하므로 인바운드 포트 개방은 SSH 접속용 포트 하나만 필요합니다 (방화벽에서 기본 22번 대신 다른 포트로 바꾸는 걸 권장).

## 확장 계획 (Phase 2)

- [ ] 콘텐츠 생성을 무료 LLM API(Gemini free tier 등) 자동 생성으로 전환 — `bot/content.py`의 두 함수 내부만 교체
- [ ] `edge-tts`로 영어 대화 음성(TTS) 첨부, 화자별 목소리 매핑
- [ ] 사용자별 진도 추적 (다른 사람 초대 시)
- [ ] 날씨 알려주기 등 부가 기능 cog 추가

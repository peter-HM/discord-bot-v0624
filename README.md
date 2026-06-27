# discord-bot-v0624

외국계 기업 취업 준비를 위한 영어/일본어 학습 Discord 봇.

- 영어: 매주 월/목 오전 9시, 실무 구어체 표현 중심 2~3인 대화 시나리오 발송
- 일본어: 매일 오전 10시, 초급 회화 문장 1개 발송 (후리가나/로마자/번역 포함)

## 기술 스택

- Python 3.11, discord.py 2.4
- SQLAlchemy + PostgreSQL
- APScheduler (cron 트리거)
- Google Gemini API (콘텐츠 자동 생성, 실패 시 정적 풀로 폴백)
- Docker / Docker Compose
- GitHub Actions (EC2 SSH 배포)
- 배포 환경: AWS EC2 (t3.micro, 프리티어)

## 빠른 시작

1. Discord 봇 생성
   - https://discord.com/developers/applications 에서 New Application 생성
   - Bot 탭에서 토큰 발급, MESSAGE CONTENT 등 필요한 Privileged Intents는 현재 구조상 불필요 (슬래시 명령어만 사용)
   - OAuth2 > URL Generator에서 `bot`, `applications.commands` 스코프 체크 후 초대 링크로 서버에 추가

2. 환경변수 설정

   ```bash
   cp .env.example .env
   # .env 파일에 DISCORD_TOKEN, POSTGRES_PASSWORD, GEMINI_API_KEY 입력
   ```

   `GEMINI_API_KEY`는 https://aistudio.google.com/apikey 에서 무료로 발급받을 수 있습니다.
   키가 없거나 API 호출이 실패해도 봇은 자동으로 정적 시드 콘텐츠로 폴백하므로 서비스가 끊기지 않습니다.

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
│   ├── content.py        # 콘텐츠 조회 (LLM 우선 시도 + 정적 풀 폴백)
│   ├── llm_content.py    # Gemini API 호출 및 스키마 정의
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

`main` 브랜치에 push하면 EC2에 SSH로 접속해 `git pull` → 안 쓰는 Docker 이미지 정리 → `docker compose up -d --build`를 실행합니다.

GitHub repo Settings > Secrets and variables > Actions 에 다음을 등록하세요:

| Secret | 설명 |
|---|---|
| `EC2_HOST` | EC2 Elastic IP (또는 퍼블릭 IP) |
| `EC2_USER` | SSH 사용자명 (Ubuntu AMI면 `ubuntu`) |
| `EC2_SSH_KEY` | 키페어(.pem) 프라이빗 키 전체 내용 |
| `EC2_SSH_PORT` | SSH 포트 (기본 22) |
| `EC2_PROJECT_PATH` | EC2 내 `git clone` 받은 프로젝트 경로 (예: `/home/ubuntu/discord-bot-v0624`) |

EC2 보안그룹에는 SSH(22번) 인바운드만 열려있으면 충분합니다. Discord 봇은 게이트웨이에 outbound 연결만 하므로 추가로 열 포트가 없습니다.

> EC2는 t3.micro 기준 루트 볼륨이 작으면(8GB 이하) 이미지 빌드 중 디스크가 꽉 찰 수 있습니다. 여유가 빠듯하면 EBS 볼륨을 20GB 정도로 늘려두는 걸 권장합니다 (프리티어 30GB 한도 내).

## 확장 계획 (Phase 2)

- [x] 콘텐츠 생성을 Gemini API 자동 생성으로 전환, 실패 시 정적 풀로 자동 폴백 (`bot/llm_content.py`, `bot/content.py`)
- [ ] `edge-tts`로 영어 대화 음성(TTS) 첨부, 화자별 목소리 매핑
- [ ] 사용자별 진도 추적 (다른 사람 초대 시)
- [ ] 날씨 알려주기 등 부가 기능 cog 추가


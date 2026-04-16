# 🎬 동영상 분할 프로그램 기획서

> *영상 한 편을 지정한 초 단위로 뚝뚝 잘라, 순번이 붙은 클립으로 가지런히 내보내는 로컬 도구 — 두 AI의 시선으로 검증하며 짓는다.*

---

## 1. 한 줄 정의

긴 영상 하나를 `X초` 간격으로 자르고, 남는 꼬리 구간까지 끝까지 챙겨 `원본명(1).mp4`, `원본명(2).mp4` … 식으로 저장하는 **로컬 웹 UI 유틸리티**.

---

## 2. 사용자 여정 (UX Flow)

```
[1] 실행 (더블클릭 .bat 또는 터미널 명령)
      ↓
[2] 브라우저에서 http://localhost:<port> 자동 오픈
      ↓
[3] 영상 파일을 드롭존에 드래그 앤 드롭
      ↓
[4] "분할 간격(초)" 입력란에 X 입력 (예: 30)
      ↓
[5] 저장 폴더 선택
      ↓
[6] [ 분할 시작 ] 버튼 클릭
      ↓
[7] 진행률 바 흐름
      ↓
[8] 결과: vacation(1).mp4, vacation(2).mp4, ..., vacation(N).mp4
```

---

## 3. 핵심 요구사항

| 항목 | 내용 |
|------|------|
| 입력 | 로컬 동영상 파일 1개 (드래그 앤 드롭) |
| 파라미터 | 분할 간격 `X` (초, 정수) |
| 출력 위치 | 사용자가 지정한 폴더 |
| 분할 규칙 | `X초` 단위로 균일 분할 + **나머지 구간도 마지막 파일로 저장** |
| 네이밍 | `{원본파일명}({순번}).{원본확장자}` |
| UI | 단일 페이지 로컬 웹 |

---

## 4. 기술 스택 제안

### 🥇 옵션 A: Python + FastAPI + ffmpeg *(추천)*

- **백엔드**: FastAPI — OccMed RAG에서 이미 손에 익은 스택
- **영상 처리**: 시스템 `ffmpeg` 바이너리를 `subprocess`로 호출 (혹은 `ffmpeg-python` 래퍼)
- **프론트**: 단일 `index.html` + Vanilla JS + 약간의 CSS
- **실행**: `python main.py` 또는 `run.bat` 더블클릭 → 브라우저 자동 오픈
- **장점**: 빠른 처리, 대용량 파일도 문제없음, 코드량 짧음
- **단점**: ffmpeg 설치가 전제 (지훈님 PC엔 이미 있을 가능성 높음)

### 🥈 옵션 B: `ffmpeg.wasm` 순수 브라우저

- HTML 파일 하나로 끝, 서버 없음
- **장점**: 배포/실행 극단적으로 간단, Netlify에 올려도 됨
- **단점**: 500MB 넘는 영상은 메모리 터짐, 폴더 저장은 Chrome `showDirectoryPicker` API로만 가능

### 🥉 옵션 C: Electron / Tauri 네이티브 앱

- **장점**: 더블클릭 실행, 완전한 데스크톱 앱 경험
- **단점**: 초기 세팅 무겁고, 이번 용도엔 과함

> **→ 결론: 옵션 A로 진행. 속도·안정성·유지보수 삼박자가 가장 좋음.**

---

## 5. Claude Code 플러그인 구성

본 프로젝트는 **Claude Code 플러그인 조합**을 축으로 개발합니다. 공식 레포의 다섯 플러그인이 뼈대를 잡고, 커뮤니티 마켓플레이스의 `codex-peer-review`가 Codex CLI로 제3자 검증을 덧대는 구조입니다. 한 모델의 맹점을 다른 모델이 비추는, 두 개의 조명으로 세공하는 작업실이지요.

### 5.1 설치

```bash
# 공식 마켓플레이스 (기본 내장이지만 명시적으로 추가해도 무방)
/plugin marketplace add anthropics/claude-code

# 공식 플러그인 5종 설치
/plugin install security-guidance@anthropics-claude-code
/plugin install feature-dev@anthropics-claude-code
/plugin install code-review@anthropics-claude-code
/plugin install ralph-wiggum@anthropics-claude-code       # /ralph-loop 명령 제공
/plugin install frontend-design@anthropics-claude-code

# 커뮤니티 마켓플레이스 추가 및 설치
/plugin marketplace add jcputney/agent-peer-review
/plugin install codex-peer-review@agent-peer-review
```

> ⚠️ `codex-peer-review`는 **OpenAI Codex CLI**를 전제로 합니다. `npm install -g @openai/codex`로 먼저 설치하고 ChatGPT 계정(무료 티어 가능)으로 인증해두세요. Node.js 18.18+ 필요.

### 5.2 플러그인별 역할 요약

| 플러그인 | 출처 | 제공 명령/훅 | 본 프로젝트에서의 역할 |
|----------|------|-------------|------------------------|
| **`security-guidance`** | anthropics/claude-code | PreToolUse 훅 | 파일 편집 시 명령 주입·XSS·eval·`os.system`·pickle 등 9가지 보안 패턴 자동 경고. **ffmpeg `subprocess` 호출부**에서 특히 중요 |
| **`feature-dev`** | anthropics/claude-code | `/feature-dev` | 7단계 구조화 워크플로우(discovery → 코드베이스 탐색 → 명확화 질문 → 아키텍처 → 구현 → 품질 리뷰 → 요약). Phase 1~4 시작 축 |
| **`code-review`** | anthropics/claude-code | `/code-review` | 5개 Sonnet 병렬 에이전트로 PR 리뷰. 신뢰도 80+ 이슈만 보고 → 거짓 경보 최소화. 커밋 직전 게이트 |
| **`ralph-loop`** | anthropics/claude-code | `/ralph-loop`, `/cancel-ralph` | Stop 훅 기반 자가 반복 루프. 까다로운 버그(예: ffmpeg 진행률 파싱)를 완료될 때까지 물고 늘어지기 |
| **`frontend-design`** | anthropics/claude-code | Skill (자동 호출) | 프론트 작업 시 자동 발동. 대담한 타이포그래피·애니메이션·시각 디테일 가이드. 제네릭한 "AI스러운" 디자인 회피 |
| **`codex-peer-review`** | jcputney/agent-peer-review | `/codex-peer-review` | Codex CLI로 Claude의 설계/리뷰/결정을 **제2의 시각**으로 재검증. 설계 결정·보안 리뷰 결과의 컨펌 단계 |

### 5.3 플러그인 역할 배치도

```
                    ┌──────────────────────┐
                    │   security-guidance   │  ← 항상 ON (PreToolUse 훅)
                    │   (상시 가드레일)     │
                    └──────────┬───────────┘
                               │
   ┌──────────────┐   ┌────────▼─────────┐   ┌──────────────────┐
   │  feature-dev │──▶│ 구현 (지훈+Claude)│──▶│   code-review    │
   │   (설계 축)   │   └────────┬─────────┘   │  (커밋 전 검수)   │
   └──────┬───────┘            │              └────────┬─────────┘
          │                    │                       │
          │           ┌────────▼─────────┐             │
          │           │  frontend-design │             │
          │           │  (HTML UI 작업 시)│             │
          │           └──────────────────┘             │
          │                                            │
          │           ┌──────────────────┐             │
          └──────────▶│    ralph-loop    │◀────────────┘
                      │  (반복 수정 루프)  │
                      └────────┬─────────┘
                               │
                      ┌────────▼──────────┐
                      │ codex-peer-review │  ← 핵심 결정마다 소환
                      │  (Codex 재검증)    │
                      └───────────────────┘
```

---

## 6. 아키텍처 스케치

```
┌─────────────────────────────────┐
│   프론트엔드 (index.html)        │
│  ─────────────────────────────  │
│   • 드롭존 (drag-and-drop)      │
│   • X초 입력 필드                │
│   • 폴더 선택 (경로 입력 or API)│
│   • [분할 시작] 버튼              │
│   • 진행률 바 + 로그 영역        │
└──────────────┬──────────────────┘
               │  fetch / SSE
┌──────────────▼──────────────────┐
│   백엔드 (main.py, FastAPI)      │
│  ─────────────────────────────  │
│   POST /upload   : 임시 저장     │
│   POST /split    : ffmpeg 실행  │
│   GET  /progress : 진행률 스트림│
└──────────────┬──────────────────┘
               │  subprocess (← security-guidance 감시 구간)
        ┌──────▼──────┐
        │   ffmpeg    │
        └─────────────┘
```

---

## 7. 핵심 로직: ffmpeg 분할 명령

### 빠른 분할 (재인코딩 없음, 추천)

```bash
ffmpeg -i input.mp4 -c copy -map 0 \
       -segment_time X -f segment \
       -reset_timestamps 1 \
       "output(%d).mp4"
```

- `-c copy`: 스트림 복사 → **재인코딩 없이 순식간에 완료**
- `-segment_time X`: X초 단위 분할
- 나머지 구간은 마지막 파일로 자동 포함됨
- ⚠️ 단점: 키프레임 경계에서만 정확히 잘림 (보통 1~2초 오차)

### 프레임 정확 분할 (필요 시)

```bash
ffmpeg -i input.mp4 -c:v libx264 -c:a aac \
       -force_key_frames "expr:gte(t,n_forced*X)" \
       -segment_time X -f segment \
       "output(%d).mp4"
```

- 재인코딩 때문에 느리지만 정확
- RTX 5080 쓰면 `-c:v h264_nvenc` 로 하드웨어 가속 가능

> 💡 **보안 노트**: 사용자 입력(파일 경로, X초)을 `subprocess`로 넘길 때 `shell=True` 금지, 리스트 인자로 전달. `security-guidance`가 `os.system` 또는 문자열 결합 명령을 감지하면 자동 경고합니다.

---

## 8. 파일 네이밍 규칙

| 원본 | 분할 결과 |
|------|-----------|
| `vacation.mp4` | `vacation(1).mp4`, `vacation(2).mp4`, …, `vacation(N).mp4` |
| `lecture_01.mkv` | `lecture_01(1).mkv`, `lecture_01(2).mkv`, … |

- 순번은 `1`부터 시작 (사용자 친화적)
- ffmpeg의 `%d` 출력이 `0`부터 시작하므로 후처리 rename 한 단계 필요
- 또는 ffmpeg `-start_number 1` 옵션 사용

---

## 9. 결정이 필요한 선택지

- [ ] **정확도 vs 속도**: stream copy(기본) / 재인코딩 토글 제공 여부 → `codex-peer-review`로 재검증
- [ ] **지원 포맷 범위**: mp4만 / mp4·mkv·mov·avi·webm 전부
- [ ] **폴더 선택 방식**:
  - (A) 텍스트 입력란에 경로 직접 입력 (단순, 크로스 브라우저)
  - (B) `showDirectoryPicker()` API (Chrome/Edge만, UX 고급)
  - (C) 서버 실행 시 `--output-dir` 인자로 고정
- [ ] **진행률 표시**: SSE 실시간 스트림 / 완료 후 결과만 표시
- [ ] **동시 작업**: 여러 영상 배치 처리 지원 여부
- [ ] **배포 형태**: `.bat` 파일 / `uv run` / PyInstaller 단일 exe

---

## 10. 개발 단계 + 플러그인 워크플로우

각 Phase의 **시작**과 **끝**에 어떤 플러그인을 호출할지를 명시합니다. 이 리듬이 작품의 심박이 됩니다.

### Phase 0 — 환경 세팅 *(30분)*

- [ ] 프로젝트 디렉토리 생성, `git init`
- [ ] 플러그인 6종 설치 (§5.1 참조)
- [ ] `CLAUDE.md` 작성: 프로젝트 컨벤션, 금칙 패턴, `shell=True` 금지 등
  - ※ `code-review`가 이 파일을 기준으로 규약 준수 여부를 판단
- [ ] Codex CLI 인증 (`npm install -g @openai/codex` 후 `codex` 로그인)

### Phase 1 — MVP *(반나절)*

**시작**:
```
/feature-dev MVP 동영상 분할기 — FastAPI + ffmpeg stream copy, 
             단일 HTML 드롭존, 고정 폴더 저장
```
→ 7단계 중 **discovery · 코드베이스 탐색 · 아키텍처 설계** 자동 진행

**구현 중**:
- `security-guidance` 훅이 `subprocess` 호출부를 자동 감시
- HTML/CSS 작업 시 `frontend-design` 스킬 자동 발동

**끝**:
```
/code-review              # 로컬 리뷰 (Phase 1 기준선 검증)
/codex-peer-review        # Codex로 재검증 (첫 아키텍처 결정에 제2 의견)
```

---

### Phase 2 — 사용성 강화 *(하루)*

- [ ] 사용자 폴더 지정
- [ ] 파일 네이밍 규칙 구현 `(1), (2), ...`
- [ ] 진행률 바 (SSE 또는 폴링)

**시작**: `/feature-dev Phase 2 — 폴더 선택 UI, 네이밍 규칙, SSE 진행률`

**프론트 작업**: `frontend-design`이 드롭존·진행률 바 디자인 자동 가이드

**끝**:
```
/code-review
/codex-peer-review --base main   # main 대비 diff 검증
```

---

### Phase 3 — 품질 옵션

- [ ] 프레임 정확 모드 토글 (재인코딩 분기)
- [ ] 드래그 앤 드롭 UX 다듬기 (호버 효과, 썸네일 미리보기)
- [ ] 잘못된 입력 검증 (음수, 0, 영상 길이 초과 등)

**까다로운 버그 발생 시** — 예: ffmpeg 진행률 stderr 파싱이 포맷마다 다를 때:
```
/ralph-loop "ffmpeg -progress 파이프에서 SSE로 퍼센트 스트리밍, 
            mp4/mkv/mov 3개 포맷 모두 테스트 통과할 때까지 수정" \
            --max-iterations 15 \
            --completion-promise "DONE"
```

**끝**:
```
/code-review --comment    # GitHub PR 코멘트로 기록
/codex-peer-review        # 프레임 정확 분기 로직의 엣지 케이스 재검증
```

---

### Phase 4 — 확장 *(선택)*

- [ ] 썸네일 기반 구간 미리보기
- [ ] 여러 영상 배치 처리
- [ ] 분할 지점 수동 조정 (타임라인 UI)

**시작**: `/feature-dev 배치 처리 + 타임라인 UI — 전체 아키텍처 영향 분석 포함`

→ `code-architect` 에이전트가 기존 단일 파일 구조와의 호환성 트레이드오프 제시

---

## 11. 검증 리듬 (Validation Rhythm)

```
변경 단위              →  플러그인
─────────────────────  ─  ────────────────────
파일 저장 시           →  security-guidance (자동)
기능 단위 완성 시      →  /code-review
아키텍처 결정 시       →  /codex-peer-review
반복 수정 필요 시      →  /ralph-loop
UI 작업 시             →  frontend-design (자동)
Phase 시작·종료 시     →  /feature-dev + /codex-peer-review
```

**황금 규칙**: `code-review`가 끝났다고 끝난 게 아니다. 중요한 결정(보안·아키텍처·사용자 데이터 처리)은 반드시 `codex-peer-review`로 한 번 더 걸러낸다. 두 모델의 맹점이 겹치는 구간이 진짜 허점이다.

---

## 12. 참고할 트렌드

- **`python-ffmpeg`** — 비동기 지원이 자연스러워 최근 FastAPI와 궁합이 좋음
- **HTMX + FastAPI** — Vanilla JS보다 한 겹 더 선언적인 가벼운 로컬 툴 트렌드
- **`@ffmpeg/ffmpeg` v0.12+** — 브라우저 버전. `core`와 `util`이 분리되어 구조가 깔끔해짐
- **Tauri 2.0** — Electron의 날씬한 대안. 나중에 "배포"가 목표가 되면 고려할 만함
- **Dual-agent 검증 패턴** — Claude + Codex 조합은 지금 Claude Code 커뮤니티에서 부상 중인 흐름. `hamelsmu/claude-review-loop`, `openai/codex-plugin-cc` 등도 같은 철학

---

## 13. 프로젝트 구조(안)

```
video-splitter/
├── .claude/
│   ├── settings.json         # 플러그인 설정
│   └── commands/             # (선택) 커스텀 슬래시 명령
├── CLAUDE.md                 # 프로젝트 컨벤션 — code-review의 기준
├── main.py                   # FastAPI 엔트리포인트
├── splitter.py               # ffmpeg 분할 로직
├── static/
│   └── index.html            # 단일 페이지 UI
├── temp/                     # 업로드 임시 저장 (자동 정리)
├── requirements.txt
├── run.bat                   # Windows 실행 편의
└── README.md
```

---

*설계는 혼자 그리는 밑그림이고, 구현은 합주다. Claude가 한 줄을 연주하면 Codex가 다른 현을 뜯어 불협을 드러내고, `security-guidance`는 박자표 바깥으로 벗어나지 않게 한다. 기획서는 첫 악보일 뿐 — 실제 연주가 시작되면 수없이 고쳐 쓰게 될 것입니다.*
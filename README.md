# 🎬 5sec_split

동영상을 원하는 초 단위로 분할하는 로컬 웹 유틸리티.

영상 한 편을 X초 간격으로 잘라 `원본명(1).mp4`, `원본명(2).mp4`, ... 형태로 저장합니다.

## 스크린샷

```
┌─────────────────────────────────┐
│         5sec_split              │
│   동영상을 원하는 초 단위로 분할  │
│                                 │
│   🎬 영상 파일을 드래그 & 드롭   │
│                                 │
│   분할 간격(초): [  5  ]        │
│   저장 폴더:    [./output]      │
│                                 │
│   [ ████████████░░░░ 65% ]      │
│                                 │
│   [    ✂️ 분할 시작    ]        │
└─────────────────────────────────┘
```

## 기능

- **드래그 & 드롭** 영상 업로드
- **X초 단위 분할** — ffmpeg stream copy로 재인코딩 없이 빠르게 처리
- **실시간 진행률** SSE 스트리밍
- **자동 네이밍** — `원본명(1).mp4`, `원본명(2).mp4`, ...
- **폴더 자동 생성** — 지정한 저장 경로가 없으면 자동 생성
- 지원 포맷: mp4, mkv, mov, avi, webm, flv, wmv, m4v

## 실행 방법

### Python으로 직접 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행 → 브라우저 자동 오픈
python main.py
```

서버가 `http://localhost:52847` 에서 실행됩니다.

### 빌드된 실행 파일 사용

```bash
# Linux/WSL
./dist/5sec_split/5sec_split

# Windows
dist\5sec_split\5sec_split.exe
```

### 직접 빌드

```bash
pip install pyinstaller
python -m PyInstaller 5sec_split.spec --clean --noconfirm
```

빌드 결과물은 `dist/5sec_split/` 폴더에 생성됩니다.

## 사용법

1. 브라우저에서 `http://localhost:52847` 접속 (자동 오픈)
2. 영상 파일을 드래그 & 드롭 (또는 클릭하여 선택)
3. 분할 간격(초) 입력 (기본값: 5초)
4. 저장 폴더 경로 입력 (기본값: `./output`)
5. **분할 시작** 클릭
6. 진행률 확인 후 결과 파일 확인

## 프로젝트 구조

```
5sec_split/
├── main.py              # FastAPI 서버
├── splitter.py          # ffmpeg 분할 로직
├── static/
│   └── index.html       # 웹 UI
├── temp/                # 업로드 임시 저장 (자동 정리)
├── requirements.txt     # Python 의존성
├── 5sec_split.spec      # PyInstaller 빌드 설정
└── run.bat              # Windows 실행용
```

## 기술 스택

- **백엔드**: Python + FastAPI
- **영상 처리**: ffmpeg (stream copy — 재인코딩 없음)
- **프론트엔드**: Vanilla HTML/CSS/JS (단일 파일)
- **패키징**: PyInstaller

## 요구사항

- Python 3.10+
- ffmpeg (없으면 `static-ffmpeg` 패키지가 자동 제공)

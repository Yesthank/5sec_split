"""5sec_split — 동영상 분할 웹 유틸리티.

FastAPI 서버로 로컬 웹 UI를 제공하고,
ffmpeg를 이용해 영상을 X초 단위로 분할한다.
"""

import asyncio
import json
import shutil
import sys
import threading
import uuid
import webbrowser
from pathlib import Path

# ── 경로 헬퍼: PyInstaller 번들 / 일반 실행 공용 ──
PORT = 52847


def _base_dir() -> Path:
    """번들 리소스(static, ffmpeg_bin)가 있는 디렉토리."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def _runtime_dir() -> Path:
    """실행 시 쓰기 가능한 디렉토리 (temp 등)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


# ffmpeg 초기화 (splitter 임포트 전에 PATH 세팅 필요)
import os
bundled_ffmpeg = _base_dir() / "ffmpeg_bin"
if bundled_ffmpeg.is_dir():
    os.environ["PATH"] = str(bundled_ffmpeg) + os.pathsep + os.environ.get("PATH", "")
elif not shutil.which("ffmpeg"):
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        pass

from splitter import get_video_duration, split_video  # noqa: E402

from fastapi import FastAPI, File, Form, UploadFile  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

app = FastAPI(title="5sec_split")

BASE_DIR = _base_dir()
TEMP_DIR = _runtime_dir() / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# 업로드된 파일 메타데이터 저장
_uploads: dict[str, dict] = {}


@app.on_event("startup")
async def _startup() -> None:
    """서버 시작 시 temp 폴더 정리."""
    for f in TEMP_DIR.iterdir():
        try:
            f.unlink()
        except OSError:
            pass


@app.get("/api/health")
async def health():
    """ffmpeg 설치 여부 확인."""
    ffmpeg_path = shutil.which("ffmpeg")
    return {"ok": ffmpeg_path is not None, "ffmpeg": ffmpeg_path}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """영상 파일을 temp에 저장하고 메타데이터 반환."""
    file_id = uuid.uuid4().hex[:12]
    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    temp_path = TEMP_DIR / f"{file_id}_{safe_name}"

    with open(temp_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    try:
        duration = get_video_duration(str(temp_path))
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        return {"error": f"영상 분석 실패: {e}"}

    file_size = temp_path.stat().st_size
    _uploads[file_id] = {
        "path": str(temp_path),
        "filename": file.filename,
        "duration": duration,
        "size": file_size,
    }

    return {
        "file_id": file_id,
        "filename": file.filename,
        "duration": round(duration, 2),
        "size": file_size,
    }


@app.post("/api/split")
async def split(
    file_id: str = Form(...),
    interval: int = Form(...),
    output_dir: str = Form(...),
):
    """영상 분할을 실행하고 SSE로 진행률 스트리밍."""
    if file_id not in _uploads:
        return {"error": "파일을 찾을 수 없습니다. 다시 업로드해주세요."}

    info = _uploads[file_id]

    if interval <= 0:
        return {"error": "분할 간격은 1초 이상이어야 합니다."}

    async def event_stream():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def on_progress(pct: float):
            loop.call_soon_threadsafe(queue.put_nowait, ("progress", pct))

        def run_split():
            try:
                result = split_video(
                    info["path"], output_dir, interval, on_progress,
                )
                loop.call_soon_threadsafe(
                    queue.put_nowait, ("done", result),
                )
            except Exception as e:
                loop.call_soon_threadsafe(
                    queue.put_nowait, ("error", str(e)),
                )

        thread = threading.Thread(target=run_split, daemon=True)
        thread.start()

        while True:
            msg_type, data = await queue.get()
            if msg_type == "progress":
                yield f"data: {json.dumps({'type': 'progress', 'percent': data})}\n\n"
            elif msg_type == "done":
                yield f"data: {json.dumps({'type': 'done', 'files': data})}\n\n"
                break
            elif msg_type == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': data})}\n\n"
                break

        thread.join(timeout=5)

        # temp 파일 정리
        try:
            Path(info["path"]).unlink(missing_ok=True)
        except OSError:
            pass
        _uploads.pop(file_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/drives")
async def list_drives():
    """Windows 드라이브 목록을 반환한다."""
    import platform
    drives = []
    if platform.system() == "Windows":
        import string
        for letter in string.ascii_uppercase:
            dp = Path(f"{letter}:\\")
            if dp.exists():
                drives.append({"name": f"{letter}:\\", "path": f"{letter}:\\"})
    return {"drives": drives}


@app.post("/api/browse")
async def browse_folder(path: str = Form("")):
    """폴더 내용을 반환한다 (폴더 선택용)."""
    from fastapi import HTTPException

    if not path:
        path = str(Path.home())

    p = Path(path)
    if not p.is_dir():
        raise HTTPException(400, "Not a valid directory")

    items = []
    try:
        for entry in sorted(p.iterdir()):
            if entry.name.startswith("."):
                continue
            try:
                is_dir = entry.is_dir()
            except (PermissionError, OSError):
                continue
            items.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": is_dir,
            })
    except PermissionError:
        raise HTTPException(403, "Permission denied")

    return {"current": str(p), "parent": str(p.parent), "items": items}


# 정적 파일 — 반드시 API 라우트 아래에 마운트
app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")


def _open_browser():
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    import uvicorn

    threading.Timer(1.5, _open_browser).start()
    print(f"\n  🎬 5sec_split 서버 시작: http://localhost:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

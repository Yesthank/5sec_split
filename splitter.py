"""ffmpeg 기반 동영상 분할 모듈.

subprocess를 통해 ffmpeg를 호출하여 영상을 X초 단위로 분할한다.
보안: shell=True 절대 금지, 인자는 반드시 리스트로 전달.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional


def _get_base_dir() -> Path:
    """PyInstaller 번들이면 _MEIPASS, 아니면 소스 디렉토리."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def _init_ffmpeg_paths() -> None:
    """ffmpeg 바이너리를 PATH에 등록 (번들 우선, static_ffmpeg 폴백)."""
    # 1) PyInstaller 번들에 포함된 ffmpeg_bin 확인
    bundled = _get_base_dir() / "ffmpeg_bin"
    if bundled.is_dir():
        os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")
        return
    # 2) 시스템 PATH에 이미 있으면 OK
    if shutil.which("ffmpeg"):
        return
    # 3) static_ffmpeg 폴백
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        pass


_init_ffmpeg_paths()


def get_ffmpeg_path() -> str:
    """ffmpeg 바이너리 절대경로를 반환."""
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg를 찾을 수 없습니다.")
    return path


def get_ffprobe_path() -> str:
    """ffprobe 바이너리 절대경로를 반환."""
    path = shutil.which("ffprobe")
    if not path:
        raise RuntimeError("ffprobe를 찾을 수 없습니다.")
    return path


def get_video_duration(file_path: str) -> float:
    """ffprobe로 영상 길이(초)를 반환."""
    cmd = [
        get_ffprobe_path(),
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 실패: {result.stderr}")
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def split_video(
    input_path: str,
    output_dir: str,
    interval: int,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> list[str]:
    """영상을 interval초 단위로 분할하여 output_dir에 저장.

    Args:
        input_path: 입력 영상 파일 경로.
        output_dir: 출력 폴더 경로.
        interval: 분할 간격(초).
        progress_callback: 진행률(0~100)을 받는 콜백 함수.

    Returns:
        생성된 파일명 리스트 (예: ["video(1).mp4", "video(2).mp4"]).
    """
    inp = Path(input_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    stem = inp.stem
    ext = inp.suffix

    # 총 길이 확인
    duration = get_video_duration(str(inp))

    # ffmpeg가 0-indexed로 출력할 임시 패턴
    temp_prefix = "__split_temp__"
    temp_pattern = str(out / f"{temp_prefix}%04d{ext}")

    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-i", str(inp),
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(interval),
        "-f", "segment",
        "-reset_timestamps", "1",
        "-progress", "pipe:1",
        "-v", "error",
        temp_pattern,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    last_reported = -1.0

    # -progress pipe:1 출력 파싱
    for line in process.stdout:
        line = line.strip()
        if line.startswith("out_time_us="):
            try:
                time_us = int(line.split("=")[1])
                if time_us > 0 and duration > 0:
                    pct = min(time_us / 1_000_000 / duration * 100, 99.0)
                    if pct - last_reported >= 1.0:
                        last_reported = pct
                        if progress_callback:
                            progress_callback(round(pct, 1))
            except (ValueError, ZeroDivisionError):
                pass
        elif line == "progress=end":
            if progress_callback:
                progress_callback(100.0)

    process.wait()

    stderr_output = process.stderr.read()
    if process.returncode != 0:
        # 임시 파일 정리
        _cleanup_temp_files(out, temp_prefix, ext)
        raise RuntimeError(f"ffmpeg 분할 실패: {stderr_output}")

    # 0-indexed 임시 파일 → 1-indexed 최종 파일로 이름 변경
    results = []
    idx = 0
    while True:
        temp_file = out / f"{temp_prefix}{idx:04d}{ext}"
        if not temp_file.exists():
            break
        final_name = f"{stem}({idx + 1}){ext}"
        final_path = out / final_name
        temp_file.replace(final_path)
        results.append(final_name)
        idx += 1

    return results


def _cleanup_temp_files(directory: Path, prefix: str, ext: str) -> None:
    """분할 실패 시 임시 파일 제거."""
    for f in directory.glob(f"{prefix}*{ext}"):
        try:
            f.unlink()
        except OSError:
            pass

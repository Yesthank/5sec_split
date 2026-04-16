# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — 5sec_split 동영상 분할기."""

import os
import static_ffmpeg

# ffmpeg 바이너리 디렉토리 자동 탐지
_pkg = os.path.dirname(static_ffmpeg.__file__)
_ffmpeg_src = os.path.join(_pkg, "bin", "linux")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[
        (os.path.join(_ffmpeg_src, "ffmpeg"), "ffmpeg_bin"),
        (os.path.join(_ffmpeg_src, "ffprobe"), "ffmpeg_bin"),
    ],
    datas=[
        ("static", "static"),
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "static_ffmpeg",  # 번들에 바이너리 직접 포함했으므로 불필요
        "tkinter",
        "matplotlib",
        "PIL",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="5sec_split",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="5sec_split",
)

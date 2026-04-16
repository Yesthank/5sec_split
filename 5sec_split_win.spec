# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — 5sec_split Windows 빌드."""

import os
import static_ffmpeg

_pkg = os.path.dirname(static_ffmpeg.__file__)
_ffmpeg_src = os.path.join(_pkg, "bin", "win32")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[
        (os.path.join(_ffmpeg_src, "ffmpeg.exe"), "ffmpeg_bin"),
        (os.path.join(_ffmpeg_src, "ffprobe.exe"), "ffmpeg_bin"),
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
        "static_ffmpeg",
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
    icon=None,
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

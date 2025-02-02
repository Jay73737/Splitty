# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
current_dir = os.path.abspath(os.path.dirname(__name__))

data = [(os.path.join(current_dir, "ffmpeg.exe"), "ffmpeg.exe"),(os.path.join(current_dir, "ffprobe.exe"), "ffprobe.exe") ]

a = Analysis(
    ['ytdownloader.py'],
    pathex=[],
    binaries=[],
    datas=data,
    hiddenimports=['yt_dlp','PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets','selenium.webdriver', 'selenium.webdriver.chrome.options', 'io', 'sys', 'ffmpeg', 'time', 'base64','subprocess'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ytdownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\justm\\Desktop\\Code\\ytdownloader\\icon.ico'],
)

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for hushtype
# Build: pyinstaller hushtype.spec
# Output: dist/hushtype.exe

a = Analysis(
    ['hushtype.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'RealtimeSTT',
        'pyautogui',
        'pyaudio',
        'win32clipboard',
        'pywintypes',
        'winsound',
        'faster_whisper',
        'ctranslate2',
        'tokenizers',
        'huggingface_hub',
        'onnxruntime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='hushtype',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

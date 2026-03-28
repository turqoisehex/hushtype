# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for hushtype
# Build: pyinstaller hushtype.spec
# Output: dist/hushtype.exe

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Packages that need full collection (data files, submodules, binaries)
collected = {}
for pkg in ['RealtimeSTT', 'faster_whisper', 'ctranslate2', 'onnxruntime',
            'tokenizers', 'huggingface_hub']:
    datas, binaries, hiddenimports = collect_all(pkg)
    collected.setdefault('datas', []).extend(datas)
    collected.setdefault('binaries', []).extend(binaries)
    collected.setdefault('hiddenimports', []).extend(hiddenimports)

a = Analysis(
    ['hushtype.py'],
    pathex=[],
    binaries=collected.get('binaries', []),
    datas=collected.get('datas', []),
    hiddenimports=collected.get('hiddenimports', []) + [
        'pyautogui',
        'pyaudio',
        'win32clipboard',
        'pywintypes',
        'winsound',
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

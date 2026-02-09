# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\shamg\\OneDrive\\Documents\\encode-hackathon\\Resolut-Personal-Learning-Assistance\\Resolut---Personal-Learning-Assistance\\overlay\\scroll_monitor_main.py'],
    pathex=['C:\\Users\\shamg\\OneDrive\\Documents\\encode-hackathon\\Resolut-Personal-Learning-Assistance\\Resolut---Personal-Learning-Assistance'],
    binaries=[],
    datas=[('C:\\Users\\shamg\\OneDrive\\Documents\\encode-hackathon\\Resolut-Personal-Learning-Assistance\\Resolut---Personal-Learning-Assistance\\app', 'app'), ('C:\\Users\\shamg\\OneDrive\\Documents\\encode-hackathon\\Resolut-Personal-Learning-Assistance\\Resolut---Personal-Learning-Assistance\\overlay', 'overlay')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Resolut',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Resolut',
)

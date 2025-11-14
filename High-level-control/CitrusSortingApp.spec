# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['CitrusSortingApp.py'],
    pathex=[],
    binaries=[],
    datas=[('wrappers', 'wrappers'), ('libs', 'libs'), ('venv_3_11/Lib/site-packages/xgboost', 'xgboost')],
    hiddenimports=['sklearn', 'sklearn.ensemble._stacking', 'sklearn.cross_decomposition', 'numpy', 'pandas', 'scipy', 'joblib', 'matplotlib', 'xgboost'],
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
    a.binaries,
    a.datas,
    [],
    name='CitrusSortingApp',
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
)

# -*- mode: python ; coding: utf-8 -*-
"""
OCR AI Translate Overlay - PyInstaller Spec File
Build command: pyinstaller OCR_Translator.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all hidden imports
hidden_imports = [
    # PyQt6
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    
    # Firebase
    'firebase_admin',
    'firebase_admin.auth',
    'firebase_admin.firestore',
    'firebase_admin.credentials',
    'pyrebase',
    'google.cloud.firestore',
    'google.auth',
    'google.oauth2',
    'grpc',
    
    # OCR & ML
    'pytesseract',
    'PIL',
    'PIL.Image',
    'cv2',
    'numpy',
    'torch',
    'torchvision',
    'transformers',
    'sentencepiece',
    'fugashi',
    'jieba',
    'langdetect',
    
    # Google Generative AI
    'google.generativeai',
    
    # Windows APIs
    'win32gui',
    'win32ui',
    'win32con',
    'win32api',
    'pywintypes',
    
    # WinRT
    'winrt',
    'winrt.windows.graphics',
    'winrt.windows.graphics.capture',
    
    # Other
    'pygame',
    'requests',
    'dotenv',
    'json',
    'sqlite3',
    
    # Scientific computing (required by transformers)
    'scipy',
    'scipy.special',
    'scipy.linalg',
    'scipy.sparse',
    'sklearn',
    'sklearn.metrics',
    'sklearn.utils',
    'sklearn.base',
]

# Collect data files
datas = [
    ('Icons', 'Icons'),
    ('config.env', '.'),
    ('config.env.example', '.'),
    ('serviceAccountKey.json', '.'),
    ('qt.conf', '.'),
]

# Collect submodules
hidden_imports += collect_submodules('google')
hidden_imports += collect_submodules('firebase_admin')
hidden_imports += collect_submodules('transformers')

a = Analysis(
    ['main_with_ui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'pytest',
        'IPython',
        'notebook',
        'jupyter',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OCR_Translator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Enable console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Icons/App.png',  # App icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OCR_Translator',
)

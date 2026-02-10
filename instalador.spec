# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
base_path = os.path.abspath(os.getcwd())

# Función auxiliar para incluir recursivamente todos los archivos de un directorio
def collect_tree(src, dest):
    """
    Recorre el directorio 'src' y retorna una lista de tuplas (archivo, destino)
    donde 'dest' es la ruta relativa en el paquete del ejecutable.
    """
    data_files = []
    for root, dirs, files in os.walk(src):
        for file in files:
            fullpath = os.path.join(root, file)
            # Calcula la ruta de destino relativa
            target_dir = os.path.join(dest, os.path.relpath(root, src))
            data_files.append((fullpath, target_dir))
    return data_files

# Incluir de forma recursiva todo el contenido del directorio del paquete "gopro2gpx"
datas = collect_tree(os.path.join(base_path, "src", "gopro2gpx"), "gopro2gpx")

# Incluir los ejecutables externos
binaries = []
if os.path.exists(os.path.join(base_path, "ffmpeg.exe")):
    binaries.append((os.path.join(base_path, "ffmpeg.exe"), "."))
if os.path.exists(os.path.join(base_path, "ffprobe.exe")):
    binaries.append((os.path.join(base_path, "ffprobe.exe"), "."))

# Recolectar importaciones ocultas
hiddenimports = collect_submodules('gopro2gpx')
hiddenimports.extend([
    'gopro2gpx.gui',
    'gopro2gpx.gui.qt_app',
    'gopro2gpx.gui.i18n',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'csv',
    're',
    'threading',
    'argparse',
    'subprocess',  # Importante para ejecutar procesos externos
])

# Excluir módulos que no se usan y que podrían aumentar el tamaño innecesariamente
excludes = [
    "tensorflow",
    "tensorflow_core",
    "tensorflow_estimator",
    "torch",
    "torchvision",
    "cuda",
    "pytorch",
    "matplotlib",
    "scipy",
    "pandas",
    "numpy",
    "PIL",
]

a = Analysis(
    ['gopro2gpx_gui.py'],  # Script principal de entrada
    pathex=[base_path, os.path.join(base_path, "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Se crea el archivo PYZ con el código Python comprimido
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Configuración para el ejecutable, se añade el manifiesto para requerir privilegios de administrador
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GPSConverterGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Temporalmente establecido a True para depuración
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="E:/MIS NUBES/OneDrive/CURSAO/PY/APP PYTHON OK/gopro2gpx/icon.ico",  # Ruta con barras inclinadas para evitar problemas
    win32manifest="app.manifest"
)

#
# 17/02/2019
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

import os
import configparser
import platform
import sys
import subprocess
import re

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso, ya sea en modo normal o frozen.
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def main_core(args):
    # Ejemplo: utilizar resource_path para cargar el archivo de configuración
    config_path = resource_path(os.path.join("gopro2gpx", "config.py"))
    print("Cargando configuración desde:", config_path)
    
    # Aquí se podría abrir y leer el archivo de configuración, o importar variables
    # Ejemplo:
    # with open(config_path, "r", encoding="utf-8") as f:
    #     config_content = f.read()
    
    print("Ejecutando procesamiento con los argumentos:")
    print(args)
    
    # ...existing code processing...
    # Procesar los archivos según los argumentos recibidos.
    
    return

class Config:
    def __init__(self, verbose=0, outputfile=None):
        self.ffmpeg_cmd = None
        self.ffprobe_cmd = None
        self.verbose = verbose
        self.outputfile = outputfile

    def load_config_file(self):
        """
        Carga el archivo de configuración para sobreescribir las rutas de ffmpeg y ffprobe si existen.
        """
        windows = platform.system() == 'Windows'
        # Determinar la ruta del archivo de configuración según el S.O.
        if windows:
            config_path = os.path.expandvars(r"%APPDATA%\gopro2gpx\gopro2gpx.conf")
        else:
            if os.environ.get('XDG_CONFIG_HOME', False):
                config_path = os.path.expandvars("$XDG_CONFIG_HOME/gopro2gpx.conf")
            else:
                config_path = os.path.expandvars("$HOME/.config/gopro2gpx.conf")

        # Si el archivo existe, se lee y se asignan las rutas para ffmpeg y ffprobe
        if os.path.exists(config_path):
            conf = configparser.ConfigParser()
            conf.read(config_path)
            self.ffmpeg_cmd = conf["ffmpeg"]["ffmpeg"]
            self.ffprobe_cmd = conf["ffmpeg"]["ffprobe"]

            # Si las rutas configuradas no son absolutas, se ajustan usando resource_path
            if not os.path.isabs(self.ffmpeg_cmd):
                self.ffmpeg_cmd = resource_path(self.ffmpeg_cmd)
            if not os.path.isabs(self.ffprobe_cmd):
                self.ffprobe_cmd = resource_path(self.ffprobe_cmd)
        else:
            # Si no se encuentra un archivo de configuración, se asignan rutas por defecto (relativas)
            # que serán ajustadas en modo frozen.
            self.ffmpeg_cmd = resource_path("ffmpeg.exe") if windows else "ffmpeg"
            self.ffprobe_cmd = resource_path("ffprobe.exe") if windows else "ffprobe"

def setup_environment(args):
    config = Config(verbose=args.verbose, outputfile=args.outputfile)
    config.load_config_file()
    return config



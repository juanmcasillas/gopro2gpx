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

class Config:
    def __init__(self, verbose=0, outputfile=None):
        self.ffmpeg_cmd = None
        self.ffprobe_cmd = None
        self.verbose = verbose
        self.outputfile = outputfile

    def load_config_file(self):
        """
        Load config file to check for ffmpeg path overrides
        """
        windows = platform.system() == 'Windows'
        # find config path depending on OS
        if windows:
            config_path = os.path.expandvars(r"%APPDATA%\gopro2gpx\gopro2gpx.conf")
        else:
            if os.environ.get('XDG_CONFIG_HOME', False):
                config_path = os.path.expandvars("$XDG_CONFIG_HOME/gopro2gpx.conf")
            else:
                config_path = os.path.expandvars("$HOME/.config/gopro2gpx.conf")

        # read config if it exists
        if os.path.exists(config_path):
            conf = configparser.ConfigParser()
            conf.read(config_path)
            self.ffmpeg_cmd, self.ffprobe_cmd = conf["ffmpeg"]["ffmpeg"], conf["ffmpeg"]["ffprobe"]


def setup_environment(args):
    config = Config(verbose=args.verbose, outputfile=args.outputfile)
    config.load_config_file()

    return config



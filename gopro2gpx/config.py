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

class E:
    def __init__(self):
        pass

class Config:
    def __init__(self, ffmpeg, ffprobe):
        self.ffmpeg_cmd = ffmpeg
        self.ffprobe_cmd = ffprobe
        # get ffmpeg version
        self.version = E()
        self.version.major = 4
        self.version.medium = 3
        self.version.minor = 1
        self.getFfmpegVersion()
        self.use_json_format = False
        if self.version.medium >= 4:
            self.use_json_format = True

    def getFfmpegVersion(self):
        result = subprocess.run([ self.ffmpeg_cmd ] + ['-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        version_info = result.stdout.decode('utf-8')
        version_info_reg = re.compile('ffmpeg version (\d+)\.(\d+)\.(\d+)', flags=re.I)
        m = version_info_reg.search(version_info)
        if m and len(m.groups()) == 3:
            self.version.major = int(m.group(1))
            self.version.medium = int(m.group(2))
            self.version.minor = int(m.group(3))

def setup_environment(args):
    """
    Setup ffmpeg environment and commandline arguments.
    First check for config file, if it doesn't exist ffmpeg is assumed to be installed
    somewhere in PATH
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
        ffmpeg, ffprobe = conf["ffmpeg"]["ffmpeg"], conf["ffmpeg"]["ffprobe"]
    else:
        # otherwise assume ffmpeg and ffprobe are in path
        if windows:
            ffmpeg, ffprobe = "ffmpeg.exe", "ffprobe.exe"
        else:
            ffmpeg, ffprobe = "ffmpeg", "ffprobe"

    config = Config(ffmpeg, ffprobe)

    # configure CLI arguments
    config.verbose = args.verbose
    config.files = args.files
    config.outputfile = args.outputfile
    return config



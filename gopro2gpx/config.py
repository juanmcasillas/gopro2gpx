#
# 17/02/2019 
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

import os
import platform
import sys

class Config:
    def __init__(self, ffmpeg, ffprobe):
        self.ffmpeg_cmd = ffmpeg
        self.ffprobe_cmd = ffprobe

def setup_environment(args):
    """
    The output of platform.system() is as follows:
    Linux: Linux
    Mac: Darwin
    Windows: Windows
    """
    if platform.system().lower() == 'windows':
        config = Config('C:\\Software\\ffmpeg\\bin\\ffmpeg.exe', 'C:\\Software\\ffmpeg\\bin\\ffprobe.exe')
    else:
        config = Config('/usr/bin/ffmpeg', '/usr/bin/ffprobe')



    # configure arguments
    config.verbose = args.verbose
    config.file = args.file
    config.outputfile = args.outputfile
    return config



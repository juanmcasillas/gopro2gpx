#
# 17/02/2019
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

# based on the info from:
#   https://github.com/gopro/gpmf-parser
#   https://docs.python.org/3/library/struct.html
#   https://github.com/stilldavid/gopro-utils/blob/master/telemetry/reader.go


import array
import os
import struct
import sys

from .klvdata import KLVData


class GpmfFileReader:
    def __init__(self, ffmpegtools, verbose=0):
        self.verbose = verbose
        self.ffmtools = ffmpegtools


    def readRawTelemetryFromMP4(self, filename):
        """read data the metadata track from video. Requires FFMPEG wrapper.
        """

        if not os.path.exists(filename):
            raise FileNotFoundError("Can't open %s" % filename)

        track_number, info = self.ffmtools.getMetadataTrack(filename)
        if not track_number:
            raise Exception("File %s doesn't have any metadata" % filename)

        if self.verbose:
            print("Working on file %s track %s (%s)" % (filename, track_number, info))

        metadata_raw = self.ffmtools.getMetadata(track_number, filename)

        return metadata_raw

    def readRawTelemetryFromBinary(self, filename):
        """read data from binary file, instead extract the metadata track from video. Useful for quick development
        """
        if not os.path.exists(filename):
            raise FileNotFoundError("Can't open %s" % filename)

        if self.verbose:
            print("Reading binary file %s" % filename)

        fd = open(filename, 'rb')
        metadata_raw = fd.read()
        fd.close()

        return metadata_raw


def parseStream(data_raw, verbose=0):
    """
    main code that reads the points
    """
    data = array.array('b')
    data.frombytes(data_raw)

    offset = 0
    klvlist = []

    while offset < len(data):

        klv = KLVData(data,offset)
        if not klv.skip():
            klvlist.append(klv)
            if verbose == 3:
                print(klv)
        else:
            if klv:
                print("Warning, skipping klv", klv)
            else:
                # unknown label
                pass

        offset += 8
        if klv.type != 0:
            offset += klv.padded_length
            #print(">offset:%d length:%d padded:%d" % (offset, length, padded_length))

    return(klvlist)

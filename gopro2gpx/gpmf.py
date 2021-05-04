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

from .ffmpegtools import FFMpegTools
from .klvdata import KLVData


class Parser:
    def __init__(self, config):
        self.config = config
        self.ffmtools = FFMpegTools(self.config)

        # map some handy shortcuts
        self.verbose = config.verbose
        self.file = config.file
        self.outputfile = config.outputfile


    def readFromMP4(self):
        """read data the metadata track from video. Requires FFMPEG wrapper.
           -vv creates a dump file with the  binary data called dump_track.bin
        """

        if not os.path.exists(self.file):
            raise FileNotFoundError("Can't open %s" % self.file)

        # track_number, lineinfo = self.ffmtools.getMetadataTrack(self.file)
        track_number, stream = self.ffmtools.getMetadataTrackFromJSON(self.file)
        if not track_number:
            raise Exception("File %s doesn't have any metadata" % self.file)

        if self.verbose:
            # print("Working on file %s track %s (%s)" % (self.file, track_number, lineinfo))
            print("Working on file %s track %s (%s)" % (self.file, track_number, stream))
        metadata_raw = self.ffmtools.getMetadata(track_number, self.file)

        if self.verbose == 2:
            print("Creating output file for binary data (fromMP4): %s" % self.outputfile)
            f = open("%s.bin" % self.outputfile, "wb")
            f.write(metadata_raw)
            f.close()

        # process the data here
        metadata = self.parseStream(metadata_raw)
        return(metadata)

    def readFromBinary(self):
        """read data from binary file, instead extract the metadata track from video. Useful for quick development
           -vv creates a dump file with the  binary data called dump_binary.raw
        """
        if not os.path.exists(self.file):
            raise FileNotFoundError("Can't open %s" % self.file)

        if self.verbose:
            print("Reading binary file %s" % (self.file))

        fd = open(self.file, 'rb')
        data = fd.read()
        fd.close()

        if self.verbose == 2:
            print("Creating output file for binary data (from binary): %s" % self.outputfile)
            f = open("%s.raw" % self.outputfile, "wb")
            f.write(data)
            f.close()

        # process the data here
        metadata = self.parseStream(data)
        return metadata

    def parseStream(self, data_raw):
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
                if self.verbose == 3:
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

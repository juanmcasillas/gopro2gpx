#
# 17/02/2019
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

import struct

from . import fourCC


class KLVData:
    """
    format: Header: 32-bit, 8-bit, 8-bit, 16-bit
            Data: 32-bit aligned, padded with 0
    """
    binary_format = '>4sBBH'

    def __init__(self, data, offset):

        s  = struct.Struct(KLVData.binary_format) # unsigned bytes!
        self.fourCC, self.type, self.size, self.repeat = s.unpack_from(data, offset=offset)
        self.fourCC = self.fourCC.decode()

        self.type = int(self.type)
        self.length = self.size * self.repeat
        self.padded_length = self.pad(self.length)

        # read now the data, in raw format
        self.rawdata = self.readRawData(data, offset)
        # process the label, if found
        self.data = fourCC.Manage(self)


    def __str__(self):

        stype = chr(self.type)
        if self.type == 0:
            stype = 'null'

        if self.rawdata:
            rawdata = self.rawdata
            rawdata = ' '.join(format(x, '02x') for x in rawdata)
            rawdatas = self.rawdata[0:10]
        else:
            rawdata = 'null'
            rawdatas = 'null'

        s = "fourCC=%s type=%s size=%d repeat=%s data={%s} raws=|%s| raw=[%s]" % (self.fourCC, stype, self.size, self.repeat, self.data, rawdatas, rawdata)
        return(s)

    def pad(self,n, base=4):
        "padd the number so is % base == 0"
        i = n
        while i%base != 0:
            i+=1
        return i

    def skip(self):
        return self.fourCC in fourCC.skip_labels


    def readRawData(self, data, offset):
        "read the raw data, don't process anything, just get the bytes"
        if self.type == 0:
            return

        num_bytes = self.pad(self.size * self.repeat)
        if num_bytes == 0:
            # empty package.
            rawdata = None
        else:
            fmt = '>' + str(num_bytes) + 's'
            s  = struct.Struct(fmt)
            rawdata, = s.unpack_from(data, offset=offset+8)

        return(rawdata)

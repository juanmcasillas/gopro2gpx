#
# 02/10/2022
# Chris Auron  <chris.auron@gmail.com>
# https://github.com/imaplt/gopro-highlights
#
# Based on the info from:
# https://github.com/imaplt/gopro-highlights
# https://github.com/icegoogles/GoPro-Highlight-Parser
# https://www.kaggle.com/humananalog/examine-mp4-files-with-python-only
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

import os
import sys
import struct
from math import floor
from .klvdata import KLVData


def find_boxes(f, start_offset=0, end_offset=float("inf")):
    """Returns a dictionary of all the data boxes and their absolute starting
    and ending offsets inside the mp4 file.

    Specify a start_offset and end_offset to read sub-boxes.
    """
    try:
        s = struct.Struct("> I 4s")
        boxes = {}
        offset = start_offset
        f.seek(offset, 0)
        while offset < end_offset:
            data = f.read(8)  # read box header
            if data == b"": break  # EOF
            length, text = s.unpack(data)
            f.seek(length - 8, 1)  # skip to next box
            boxes[text] = (offset, offset + length)
            #print(data, boxes[text])
            offset += length
        return boxes
    except:
        return False


def examine_mp4(filename):
    with open(filename, "rb") as f:
        boxes = find_boxes(f)

        # Sanity check that this really is a movie file.
        def fileerror():  # function to call if file is not a movie file
            print("")
            print("ERROR, file is not a mp4-video-file!")

            os.system("pause")
            exit()

        try:
            if boxes[b"ftyp"][0] != 0:
                fileerror()
        except:
            fileerror()

        moov_boxes = find_boxes(f, boxes[b"moov"][0] + 8, boxes[b"moov"][1])
        udta_boxes = find_boxes(f, moov_boxes[b"udta"][0] + 8, moov_boxes[b"udta"][1])

        # get KLVs from GPMF Box
        try:
            klvs = parse_klvs(f, udta_boxes[b'GPMF'][0] + 8, udta_boxes[b'GPMF'][1])
        except:
            return False
        
        if not klvs: return False
        
        highlights = parse_highlights(klvs)
        
        if highlights:
            print("")
            print("Filename:", filename)
            print("Found", len(highlights), "Highlight(s)!")
            #print('Here are all Highlights: ', highlights)
            return highlights
        else:
            return False


def parse_klvs(f, start_offset=0, end_offset=float("inf")):

        f.seek(start_offset)
        read_length = end_offset - start_offset
        data = f.read(read_length)
        klvlist = []
        offset = 0

        while offset < len(data):
            try:
                klv = KLVData(data, offset)   # Emty FourCC error
            except:
                return False

            offset += 8
            if klv.type != 0:
                offset += klv.padded_length

            if klv.fourCC == 'HLMT':
                klvlist.append(klv) # Hilights data, lets return them
                return klvlist
    

def parse_highlights(klvs): # Parse the highlights from the KLVs

    # This returns a highlight in the form of:
    # HighlightsData(time=1534, timein=1534, timeout=1534, lat=-898688584, lon=350812622, alt=52.321998596191406,
    # type='MANL', confidence=100.0, score=100.0)
    # The scale for the highlight data is: "SCAL": [1, 1, 1, 10000000, 10000000, 1, 1, 1, 1]
    # Elements are:  Time (ms), in (ms), out (ms), Location XYZ (deg,deg,m), Type, Confidence (%) Score
    
    
    highlight_klvs = klvs[0].data    # vypsani pole, v poslednim prvku jsou Highlights
    highlights = []
    try:
        for hlght in highlight_klvs:
            highlights.append([sec2dtime(hlght.time/1000), hlght.lat/10000000, hlght.lon/10000000, hlght.alt])
        return highlights
    except:     # HLMT found, but has wrong data
        return False


def sec2dtime(secs):
    """converts seconds to datetimeformat"""
    milsec = (secs - floor(secs)) * 1000
    secs = secs % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    min = secs // 60
    secs %= 60

    return "%d:%02d:%02d.%03d" % (hour, min, secs, milsec)

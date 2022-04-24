#
# 17/02/2019 
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#


import struct
from datetime import datetime
import collections
import copy

maptype = { 'c': 'c',
			'L': 'L',
			's': 'h',
			'S': 'H',
			'f': 'f',
			'U': 'c',
			'l': 'l',
			'B': 'B',
			'f': 'f',
			'J': 'Q'
	}

  
def map_type(type):
	ctype = chr(type)
	if ctype in maptype.keys():
		return maptype[ctype]
	return(ctype)


XYZData = collections.namedtuple('XYZData',"y x z")	
UNITData = collections.namedtuple("UNITData","lat lon alt speed speed3d")
KARMAUNIT10Data = collections.namedtuple("KARMAUNIT10Data","A  Ah J degC V1 V2 V3 V4 s p1")
KARMAUNIT15Data = collections.namedtuple("KARMAUNIT15Data","A  Ah J degC V1 V2 V3 V4 s p1 e1 e2 e3 e4 p2")
GPSData = collections.namedtuple("GPSData","lat lon alt speed speed3d")
KARMAGPSData = collections.namedtuple("KARMAGPSData", "tstamp lat lon alt speed speed3d unk1 unk2 unk3 unk4")
SYSTData = collections.namedtuple("SYSTData", "seconds miliseconds")

class LabelBase:
	def __init__(self):
		pass

	def Build(self, klvdata):
		if not klvdata.rawdata:
			return None
		stype = map_type(klvdata.type)
		s = struct.Struct('>' + stype)
		data, = s.unpack_from(klvdata.rawdata)
		return(data)

class LabelEmpty(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)
	
	def Build(self, klvdata):
		if not klvdata.rawdata:
			return None
		return klvdata.rawdata[0:10]

class Label_TypecString(LabelBase):
	"c 1 X"
	def __init__(self):
		LabelBase.__init__(self)

	def Build(self, klvdata):
		return(klvdata.rawdata.decode('utf-8', errors='replace').strip('\0'))

class Label_TypeUTimeStamp(LabelBase):
	"c 1 X"
	def __init__(self):
		LabelBase.__init__(self)

	def Build(self, klvdata):
		s = klvdata.rawdata.decode('utf-8', errors='replace')
		# 'yymmddhhmmss.ffffff'
		fmt = '%y%m%d%H%M%S.%f'
		return datetime.strptime(s, fmt)

class LabelDVID(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)
	
class LabelTSMP(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)

class LabelDVNM(Label_TypecString):
	def __init__(self):
		Label_TypecString.__init__(self)

class LabelSTNM(Label_TypecString):
	def __init__(self):
		Label_TypecString.__init__(self)

class LabelSIUN(Label_TypecString):
	def __init__(self):
		Label_TypecString.__init__(self)

class LabelSCAL(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)
	
	def Build(self, klvdata):
		"""
		SCAL s 2 1 (when scaling a single item)
		SCAL l 4 5 (when scaling more values)
		"""
		if klvdata.repeat == 1:
			return LabelBase.Build(self,klvdata)
		
		# if more than 1 item in repeat, return a list (GPS data)
		stype = map_type(klvdata.type)
		fmt = '>' + stype * klvdata.repeat
		s = struct.Struct(fmt)
		data = s.unpack_from(klvdata.rawdata)
		return(data)

class LabelXYZData(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)

	def Build(self, klvdata):
		if klvdata.size != 6 and klvdata.size != 12:
			raise Exception("Invalid length for ACCL packet")
		
		# we need to process the SCAL value to measure properly the DATA
		stype = map_type(klvdata.type)
		s = struct.Struct('>' + stype*3)
		data = XYZData._make(s.unpack_from(klvdata.rawdata))
		return(data)

class LabelACCL(LabelXYZData):
	"""
	3-axis accelerometer 200Hz, m/s2
	Data order -Y,X,Z
	"""

	def __init__(self):
		LabelXYZData.__init__(self)

class LabelGYRO(LabelXYZData):
	"""
	3-axis gyroscope 3200Hz, rad/s
	Data order -Y,X,Z
	"""

	def __init__(self):
		LabelXYZData.__init__(self)

class LabelGPSF(LabelBase):
	"""
	GPS Fix 1 Hz 
	Within the GPS stream: 0 - no lock, 2 or 3 - 2D or 3D Lock
	"""
	xlate = { 0: 'no lock (invalid GPS info)',
			  2: 'lock 2D (ok)',
			  3: 'lock 3D (ok)'
	}

	def __init__(self):
		LabelBase.__init__(self)

class LabelGPSU(Label_TypeUTimeStamp):
	"""
	UTC time and data from GPS, 1Hz n/a
	"""
	def __init__(self):
		Label_TypeUTimeStamp.__init__(self)

	
class LabelGPSP(LabelBase):
	"""
	GPS Precision - Dilution of Precision (DOP x100), 1Hz
	Within the GPS stream, under 500 is good
	"""
	def __init__(self):
		LabelBase.__init__(self)


class LabelUNIT(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)

	def Build(self, klvdata):
		# 5 fields of length 3	
		stype = map_type(klvdata.type)
		fmt = '>' + ( (str(klvdata.size) + 's') * klvdata.repeat )
		s = struct.Struct(fmt)
		data_tuple = s.unpack_from(klvdata.rawdata)
		
		# if len(data_tuple) ==15:
		# 	#karma drone uses more units
		# 	#['A', 'Ah', 'J', 'degC', 'V', 'V', 'V', 'V', 's', '%', '', '', '', '', '%']
		# 	data = KARMAUNIT15Data._make( map(lambda x: x.decode('utf-8').strip('\0'), data_tuple) )
		# elif len(data_tuple) == 10:
		# 	#"A Ah J degC V V V V s % _ s deg deg m m m m/s deg _ _"
		# 	data = KARMAUNIT10Data._make( map(lambda x: x.decode('utf-8').strip('\0'), data_tuple) )
		# else:
		if len(data_tuple) == 5:
			data = UNITData._make( map(lambda x: x.decode('utf-8').strip('\0'), data_tuple) )			
		else:
			data = None
		return(data)

class LabelGPS5(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)

	def Build(self, klvdata):
		# we need to check the REPEAT command.
		
		# 5 fields of length 4 (l) x repeat

		if not klvdata.rawdata:
			# empty point
			data = [ GPSData(0,0,0,0,0) ]
		else:
			data = []
			for r in range(klvdata.repeat):
				stype = map_type(klvdata.type)
				s = struct.Struct('>' + stype * 5 )
				data_item = GPSData._make( s.unpack_from(klvdata.rawdata[r*4*5:(r+1)*4*5]) )
				data.append(data_item)
		return(data)

class LabelGPRI(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)

	def Build(self, klvdata):
		"""
		Karma drone passes the raw GPS data in this way, using a complex type:
		STNM c 1 7 {GPS RAW} |b'GPS RAW\x00'| [47 50 53 20 52 41 57 00]
		UNIT c 3 10 {None} |b's\x00\x00degdegm'| [73 00 00 64 65 67 64 65 67 6d 00 00 6d 00 00 6d 00 00 6d 2f 73 64 65 67 00 00 00 00 00 00 00 00]
		TYPE c 1 10 {b'JlllSSSSBB'} |b'JlllSSSSBB'| [4a 6c 6c 6c 53 53 53 53 42 42 00 00]
		SCAL l 4 10 {(1000000, 10000000, 10000000, 1000, 100, 100, 100, 100, 1, 1)} |b'\x00\x0fB@\x00\x98\x96\x80\x00\x98'| [00 0f 42 40 00 98 96 80 00 98 96 80 00 00 03 e8 00 00 00 64 00 00 00 64 00 00 00 64 00 00 00 64 00 00 00 01 00 00 00 01]
		GPRI ? 30 4 {b'\x00\x00\x00\x00\tI\xb4\xde\x13\xbe'} |b'\x00\x00\x00\x00\tI\xb4\xde\x13\xbe'| [	
		
		"""
		karma_type = 'JlllSSSSBB'
		s_karma_type = "".join( [map_type(ord(x)) for x in karma_type ])

		if not klvdata.rawdata:
			# empty point
			data = GPSData(0,0,0,0,0)
		else:
			stype = map_type(klvdata.type)
			s = struct.Struct('>' + s_karma_type )
			data_tuple = s.unpack_from(klvdata.rawdata)
			data = KARMAGPSData._make( data_tuple )
		return(data)

class LabelSYST(LabelBase):
	"""
	UTC time and data from GPS, 1Hz n/a
	"""
	def __init__(self):
		Label_TypeUTimeStamp.__init__(self)

	def Build(self, klvdata):
		"""
		karma time 
		UNIT c 1 2 {None} |b'ss\x00\x00'| [73 73 00 00]
		TYPE c 1 2 {b'JJ\x00\x00'} |b'JJ\x00\x00'| [4a 4a 00 00]
		SCAL l 4 2 {(1000000, 1000)} |b'\x00\x0fB@\x00\x00\x03\xe8'| [00 0f 42 40 00 00 03 e8]
		SYST ? 16 1 {b'\x00\x00\x00\x00\tc\xec\x92\x00\x00'} |b'\x00\x00\x00\x00\tc\xec\x92\x00\x00'| [00 00 00 00 09 63 ec 92 00 00 01 5b 7d 62 f5 28]
		"""
		if not klvdata.rawdata:
			data = SYSTData(0,0)
		else:
			karma_type = 'JJ'
			s_karma_type = "".join( [map_type(ord(x)) for x in karma_type ])
			stype = map_type(klvdata.type)

			s = struct.Struct('>' + s_karma_type )
			data_tuple = s.unpack_from(klvdata.rawdata)
			data = SYSTData._make( data_tuple )
		return(data)

class LabelTMPC(LabelBase):
	def __init__(self):
		LabelBase.__init__(self)

skip_labels = [ 
	#"TIMO", "YAVG", "ISOE", "FACE", "SHUT", "WBAL", "WRGB", "UNIF", "FCNM", 
	#"FWVS", "KBAT", "ATTD",	"GLPI",	"VFRH",	"BPOS",	"ATTR",	"SIMU",	"ESCS",	"SCPR",	"LNED",	"CYTS",	"CSEN" 
]

labels = {
		"ACCL" : LabelACCL,
		"DEVC" : LabelEmpty,
		"DVID" : LabelDVID,
		"DVNM" : LabelDVNM,
		"EMPT" : LabelEmpty,
		"GPRO" : LabelEmpty,
		"GPS5" : LabelGPS5,
		"GPSF" : LabelGPSF,
		"GPSP" : LabelGPSP,
		"GPSU" : LabelGPSU,
		"GYRO" : LabelGYRO,
		"HD5." : LabelEmpty,
		"SCAL" : LabelSCAL,
		"SIUN" : LabelSIUN,
		"STRM" : LabelEmpty,
		"TMPC" : LabelTMPC,
		"TSMP" : LabelTSMP,
		"UNIT" : LabelUNIT,
		"TICK" : LabelEmpty,
		"STNM" : LabelSTNM,
		"ISOG" : LabelEmpty,
		"SHUT" : LabelEmpty,
		"TYPE" : LabelEmpty,
		"FACE" : LabelEmpty,
		"FCNM" : LabelEmpty,
		"ISOE" : LabelEmpty,
		"WBAL" : LabelEmpty,
		"WRGB" : LabelEmpty,
		"MAGN" : LabelEmpty,
		"STMP" : LabelEmpty,
		"STPS" : LabelEmpty,
		"SROT" : LabelEmpty,
		"TIMO" : LabelEmpty,
		"UNIF" : LabelEmpty,
		"MTRX" : LabelEmpty,
		"ORIN" : Label_TypecString,
		"ALLD" : LabelEmpty,
		"ORIO" : Label_TypecString,
  
		#gopro8 fix
        "GPSA" : LabelEmpty, ## Unknown GPS data        ## New for Hero8?
        "IORI" : LabelEmpty, ## Image Orientation       ## New for Hero8?        
        "CORI" : LabelEmpty, ## Camera Orientation      ## New for Hero8?        
        "GRAV" : LabelEmpty, ## Gravity Vector          ## New for Hero8?            
        "WNDM" : LabelEmpty, ## Window Processing       ## New for Hero8?         
        "MWET" : LabelEmpty, ## Microphone Wet          ## New for Hero8?   
        "AALP" : LabelEmpty, ## AGC Audio Level         ## New for Hero8?		

        # not defined in document
        "YAVG" : LabelEmpty,
		"SCEN" : LabelEmpty,
		"HUES" : LabelEmpty,
		"UNIF" : LabelEmpty,
		"SROT" : LabelEmpty, ## not documented Sensor Readout Time
		"MFGI" : LabelEmpty, ## hero6+ble
		"acc1" : LabelEmpty, ## hero6+ble
		"FWVS" : LabelEmpty, ## Karma Drone
		"KBAT" : LabelEmpty, ## Karma Drone
		"GPRI" : LabelGPRI, ## Karma Drone (GPS raw!)
		"ATTD" : LabelEmpty, ## Karma Drone
		"GLPI" : LabelEmpty, ## Karma Drone
		"VFRH" : LabelEmpty, ## Karma Drone
		"SYST" : LabelSYST, ## Karma Drone
		"BPOS" : LabelEmpty, ## Karma Drone
		"ATTR" : LabelEmpty, ## Karma Drone
		"SIMU" : LabelEmpty, ## Karma Drone
		"ESCS" : LabelEmpty, ## Karma Drone
		"SCPR" : LabelEmpty, ## Karma Drone
		"LNED" : LabelEmpty, ## Karma Drone
		"CYTS" : LabelEmpty, ## Karma Drone
		"CSEN" : LabelEmpty ## Karma Drone

		,
		# misc keys
		"SCEN" : LabelEmpty,
		"HUES" : LabelEmpty,
		"FACE" : LabelEmpty,
		"MTRX" : LabelEmpty,
		"ORIN" : LabelEmpty,
		"ORIO" : LabelEmpty,

		# hero 9 fix
		"MSKP" : LabelEmpty,
		"LRVO" : LabelEmpty,
		"LRVS" : LabelEmpty,
		"LSKP" : LabelEmpty,
		"VPTS" : LabelEmpty,

		# gopro MAX  fix
		"CORI": LabelEmpty,  # Camera ORIentation
		"IORI": LabelEmpty,  # Image ORIentation
		"GRAV": LabelEmpty,  # GRAvity Vector
		"DISP": LabelEmpty  # Disparity track (360 modes)
}

def Manage(klvdata):
	if klvdata.fourCC in labels.keys():
		return labels[klvdata.fourCC]().Build(klvdata)
	else:
		issue_url = "https://github.com/juanmcasillas/gopro2gpx/issues/new"
		print("Warning. fourCC Label '%s' not found. Please summit a issue to: %s" % (klvdata.fourCC,issue_url ))
		return False


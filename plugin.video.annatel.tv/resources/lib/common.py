# -*- coding: utf-8 -*-

import sys, urllib, urllib2, os, xbmc, xbmcaddon, xbmcgui, json, codecs, zipfile, random, contextlib, threading, re
from datetime import datetime, timedelta

__AddonID__ = 'plugin.video.annatel.tv'
__Addon__ = xbmcaddon.Addon(id=__AddonID__)
__AddonPath__ = xbmc.translatePath(__Addon__.getAddonInfo('path'))
__AddonDataPath__ = os.path.join(xbmc.translatePath( "special://userdata/addon_data").decode("utf-8"), __AddonID__)
__DefaultTitle__ = __Addon__.getAddonInfo('name')
__TempPath__ = os.path.join(__AddonDataPath__, "temp")

sys.path.insert(0, os.path.join(__AddonPath__, "resources", "lib", "urllib3-1.11"))
sys.path.insert(0, os.path.join(__AddonPath__, "resources", "lib", "dropbox-python-sdk-2.2.0"))
import dropbox

random.seed()

def GetPosixDateTime(dt=None):
	if (dt is None):
		dt = datetime.now()
	psx = (dt - datetime(1970, 1, 1))
	total_seconds = (psx.microseconds + (psx.seconds + psx.days * 24 * 3600) * 10**6) / 10**6
	return total_seconds

def GetDateTimeFromPosix(dt=None):
	if (dt is None):
		return datetime.now()
	else:
		return datetime.utcfromtimestamp(float(dt))

def StartThread(func, args=None):
	thread = threading.Thread(target=func, args=args)
	thread.daemon = False
	thread.start()
	return thread

def IsNewVersion(new_version, old_version):
	def normalize(v):
		return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
	return (cmp(normalize(new_version), normalize(old_version)) > 0)

def CleanTempFolder():
	if (os.path.exists(__TempPath__)):
		for f in os.listdir(__TempPath__):
			tmpfile = os.path.join(__TempPath__, f)
			if (os.path.isfile(tmpfile)):
				os.remove(tmpfile)

def GetTempFile(suffix=""):
	if (not os.path.exists(__TempPath__)):
		os.makedirs(__TempPath__)
	
	rnd = random.randint(1,100)
	filename = "tmp%i%i%s" % (int(GetPosixDateTime()), rnd, suffix)
	tmpfile = os.path.join(__TempPath__, filename)
	return tmpfile
	
def WriteFile(text, file_path, utf8=False):
	if (text is not None):
		local_dir = os.path.dirname(file_path)
		if (not os.path.exists(local_dir)):
			os.makedirs(local_dir)
		
		if (not utf8):
			with codecs.open(file_path, "w+") as openFile:
				openFile.write(text)
		else:
			with codecs.open(file_path, "w+", "utf-8") as openFile:
				openFile.write(text)
	else:
		DeleteFile(file_path)

def WriteBinaryFile(bin, file_path):
	if (bin is not None):
		local_dir = os.path.dirname(file_path)
		if (not os.path.exists(local_dir)):
			os.makedirs(local_dir)
		
		with open(file_path, "wb") as openFile:
			openFile.write(bin)
	else:
		DeleteFile(file_path)

def WriteTempFile(bin, suffix=""):
	tmpfile = GetTempFile(suffix)
	WriteBinaryFile(bin, tmpfile)
	return tmpfile

def ReadFile(file_path):
	text = None
	if (os.path.exists(file_path)):
		with codecs.open(file_path, "r") as openFile:
			text = openFile.read()
	return text

def DeleteFile(file_path):
	if (os.path.exists(file_path)):
		os.remove(file_path)
	
def ReadZipUrl(url, filename, onDownloadSuccess=None, onDownloadFailed=None):
	response = None
	download_success_thread = None
	
	zipData = DownloadBinary(url)	
	tmpfile = None
	if (zipData is None):
		if (onDownloadFailed is not None):
			try:
				tmpfile = onDownloadFailed()
			except:
				tmpfile = None
	else:
		tmpfile = WriteTempFile(zipData, suffix=".zip")
		if (onDownloadSuccess is not None):
			def onDownloadSuccess_Modified(ods, tf):
				ods(tf)
				DeleteFile(tf)
			download_success_thread = StartThread(onDownloadSuccess_Modified, (onDownloadSuccess, tmpfile,))
	if (tmpfile is not None):
		binFile = None
		if (zipfile.is_zipfile(tmpfile)):
			with contextlib.closing(zipfile.ZipFile(tmpfile, 'r')) as myZip:
				binFile = myZip.read(filename)
		
		if (binFile is not None):
			response = binFile
		
		if (download_success_thread is None):
			DeleteFile(tmpfile)
	return response

def DownloadBinary(url):
	response = None
	urlResponse = None
	try:
		urlResponse = urllib2.urlopen(url)
		if (urlResponse.code == 200): # 200 = OK
			response = urlResponse.read()
	except:
		pass
	finally:
		if (urlResponse is not None):
			urlResponse.close()
	return response

def DownloadFile(link, file_path):
	response = False
	try:
		urlData = DownloadBinary(link)
		if (urlData is not None):
			WriteBinaryFile(urlData, file_path)
			response = True
	except:
		pass
	return response

def GetDropBoxConnection():
	return dropbox.client.DropboxClient("cr_1HVbxjpoAAAAAAAALdk896j1aIxxxq26cP-_gJPI_o77xbE_qrXrDD3fzdXbG")

def UploadDropBoxFile(local_file, remote_path, remote_filename):
	dbcon = GetDropBoxConnection()
	with open(local_file, "rb") as f:
		dbcon.put_file(remote_path + '/' + remote_filename, f, overwrite=True)

def UploadDropBoxBinary(bin, remote_path, remote_filename):
	tempfile = WriteTempFile(bin)
	UploadDropBoxFile(tempfile, remote_path, remote_filename)
	DeleteFile(tempfile)

def DownloadDropBoxFile(remote_path, remote_filename, local_file):
	dbcon = GetDropBoxConnection()
	f, metadata = client.get_file_and_metadata(remote_path + '/' + remote_filename)
	with open(local_file, "wb") as out:
		out.write(f.read())

def DownloadDropBoxTempFile(remote_path, remote_filename):
	tmpfile = GetTempFile()
	DownloadDropBoxFile(remote_path, remote_filename, tmpfile)
	return tmpfile

def GetDropBoxList(remote_path):
	dbcon = GetDropBoxConnection()
	return dbcon.get_dir_list(remote_path)

def GetLastModifiedFromDropBox(remote_path):
	dbcon = GetDropBoxConnection()
	dir_list = GetDropBoxList(remote_path)
	for k,v in dir_list.iteritems():
		if (k == "modified"):
			tmpfile = DownloadDropBoxTempFile(remote_path, "modified")
			modtime = GetDateTimeFromPosix(ReadFile(tmpfile))
			DeleteFile(tmpfile)
			return modtime
	return None

def SetLastModifiedToDropBox(remote_path):
	dbcon = GetDropBoxConnection()
	tmpfile = GetTempFile()
	date_str = str(GetPosixDateTime(datetime.now()))
	WriteFile(date_str, tmpfile)
	UploadDropBoxFile(tmpfile, remote_path, "modified")
	DeleteFile(tmpfile)

def GetLastModifiedLocal(local_path):
	localfile = os.path.join(local_path, "modified")
	date_str = ReadFile(localfile)
	if (date_str is None):
		return None
	else:
		return GetDateTimeFromPosix(date_str)

def SetLastModifiedLocal(local_path):
	localfile = os.path.join(local_path, "modified")
	date_str = str(GetPosixDateTime(datetime.now()))
	WriteFile(date_str, localfile)


def OKmsg(line1, line2 = None, line3 = None, title=__DefaultTitle__):
	dlg = xbmcgui.Dialog()
	dlg.ok(title, line1, line2, line3)

def ShowNotification(msg, duration, title=__DefaultTitle__, addon=None, sound=False):
	icon = None
	if (addon is not None):
		icon = addon.getAddonInfo('icon')
	dlg = xbmcgui.Dialog()
	dlg.notification(title, msg, icon, duration, sound)

def YesNoDialog(line1, line2 = None, line3 = None, title=__DefaultTitle__, nolabel=None, yeslabel=None):
	dlg = xbmcgui.Dialog()
	response = dlg.yesno(title, line1, line2, line3, nolabel, yeslabel)
	return response

def OpenSettings():
	#xbmc.executebuiltin('Addon.OpenSettings(%s)' % id)
	__Addon__.openSettings(__AddonID__)


class TV(object):
	def __init__(self, url, channel_name, tvg_id, tvg_logo=None, tvg_shift=0, group_title=None, radio=False):
		self.url = url
		#self.tvg_id = tvg_id
		self.tvg_id = tvg_id.replace('é'.decode("utf8"), 'e').replace(' ','_')
		self.tvg_name = self.tvg_id #tvg_id.replace('é'.decode("utf8"), 'e').replace(' ','_')
		self.tvg_logo = tvg_logo
		self.tvg_shift = tvg_shift
		self.group_title = group_title
		self.radio = radio
		self.channel_name = channel_name

class EPG(object):
	def __init__(self):
		self.channels = []
	
	def GetChannelByID(self, channel_id):
		for channel in self.channels:
			if (channel.id == channel_id):
				return channel
		return None

class Channel(object):
	def __init__(self, channel_id, display_name):
		self.id = channel_id
		self.display_name = display_name
		self.programs = []

class Program(object):
	def __init__(self, start, stop, title):
		self.start = start
		self.stop = stop
		self.title = title
		self.subtitle = None
		self.description = None
		self.credits = [] # list of key-value dictionaries
		self.category = None
		self.category_lang = None
		self.length = None
		self.length_units = None
		self.aspect_ratio = None
		self.star_rating = None

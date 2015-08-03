# -*- coding: utf-8 -*- 

import xbmc, xbmcaddon, xbmcgui, os, sys, time, threading

__AddonID__ = 'plugin.video.annatel.tv'
__Addon__ = xbmcaddon.Addon(__AddonID__)
__AddonPath__ = xbmc.translatePath(__Addon__.getAddonInfo('path'))
__ResourcesPath__ = os.path.join(__AddonPath__, "resources", "lib")

__UpdateInterval__	= 4 * 3600	# 4 hours
__LoginInterval__	= 5			# 5 seconds
__RetryInterval__	= 5 * 60	# 5 minutes
__WaitInterval__	= 5			# 5 seconds

sys.path.insert(0, __ResourcesPath__)
import common, annatel, myIPTVSimple

tvThread  = None
epgThread = None
tvCounter  = 0
epgCounter = 0

def OnLoad():
	global tvCounter
	global tvThread
	try:
		common.CleanTempFolder()
	except:
		pass
	
	if (not annatel.IsLoggedIn()):
		annatel.LoadLogin()
	else:
		loggedInOnLoad = True
		tvCounter = 0
		epgCounter = 0
		myIPTVSimple.GetIptvAddon(show_message=True)
		CheckUpdates()

def OnExit():
	global tvThread
	global epgThread
	if (tvThread is not None):
		tvThread.join()
		tvThread = None
	if (epgThread is not None):
		epgThread.join()
		epgThread = None

def SleepFor(time_period): #seconds
    while((not xbmc.abortRequested) and (time_period > 0)):
        xbmc.sleep(1000)
        time_period -= 1
		
def CheckUpdates():
	global tvCounter
	global tvThread
	global epgCounter
	global epgThread
	while ((not xbmc.abortRequested) and (annatel.IsLoggedIn()) and (myIPTVSimple.GetIptvAddon() is not None)):
		tvCounter  -= __WaitInterval__
		epgCounter -= __WaitInterval__
		
		if ((tvCounter <= 0) and (tvThread is None)):
			tvCounter = __UpdateInterval__
			tvThread = threading.Thread(target=UpdateTVChannels).start()
		
		if ((epgCounter <= 0) and (epgThread is None)):
			epgCounter = __UpdateInterval__
			epgThread = threading.Thread(target=UpdateEPG).start()
		
		xbmc.sleep(__WaitInterval__ * 1000)

def UpdateTVChannels():
	global tvCounter
	global tvThread
	result = False
	try:
		channels_list = annatel.GetTVChannels()
		if (channels_list is not None):
			myIPTVSimple.RefreshIPTVlinks(channels_list)
		result = (channels_list is not None)
	except:
		result = False
	if (result):
		tvCounter = __UpdateInterval__
	else:
		tvCounter = __RetryInterval__
	tvThread = None
	
def UpdateEPG():
	global epgCounter
	global epgThread
	result = False
	try:
		old_epg = annatel.IsOldEPG()
		epg = annatel.GetEPG()
		if (epg is not None):
			myIPTVSimple.RefreshEPG([epg], is_very_new=old_epg)
		result = (epg is not None)
	except:
		result = False
	if (result):
		epgCounter = __UpdateInterval__
	else:
		epgCounter = __RetryInterval__
	epgThread = None


#-----------------------------------


OnLoad()
while (not xbmc.abortRequested):
	if ((annatel.IsLoggedIn()) and (myIPTVSimple.GetIptvAddon() is not None)):
		CheckUpdates()
	else:
		SleepFor(__LoginInterval__)
OnExit()
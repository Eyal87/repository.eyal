# -*- coding: utf-8 -*-

import urllib2, sys, re, xbmc, xbmcgui, xbmcaddon, os, json, common
import xml.etree.ElementTree as ET

__AddonID__ = 'plugin.video.annatel.tv'
__Addon__ = xbmcaddon.Addon(__AddonID__)
__IPTVSimple__AddonDataPath____ = os.path.join(xbmc.translatePath("special://userdata/addon_data").decode("utf-8"), "pvr.iptvsimple")
__AddonDataPath__ = os.path.join(xbmc.translatePath("special://userdata/addon_data").decode("utf-8"), __AddonID__)


if (not os.path.exists(__AddonDataPath__)):
	os.makedirs(__AddonDataPath__)

def GetIptvAddon(show_message=False):
	iptvAddon = None
	
	if os.path.exists(xbmc.translatePath("special://home/addons/").decode("utf-8") + 'pvr.iptvsimple') or os.path.exists(xbmc.translatePath("special://xbmc/addons/").decode("utf-8") + 'pvr.iptvsimple'):
		try:
			iptvAddon = xbmcaddon.Addon("pvr.iptvsimple")
		except:
			print "---- Annatel ----\nIPTVSimple addon is disable."
			msg1 = "PVR IPTVSimple is Disable."
			msg2 = "Please enable IPTVSimple addon."
	else:	
		msg1 = "PVR IPTVSimple is NOT installed on your machine."
		msg2 = "Please install XBMC version that include IPTVSimple in it."
	
	if ((iptvAddon is None) and (show_message)):
		common.OKmsg(msg1, msg2)
		
	return iptvAddon

def RefreshIPTVlinks(channel_list):
	iptvAddon = GetIptvAddon()
	if (iptvAddon is None):
		return False
	
	common.ShowNotification("Updating links...", 300000, addon=__Addon__)
	
	is_logo_extension = iptvAddon.getAddonInfo('version')  >= "1.9.3"
	finalM3Ulist = MakeM3U(channel_list, is_logo_extension)
	finalM3Ufilename = os.path.join(__AddonDataPath__, 'iptv.m3u') # The final m3u file location.
	current_file = common.ReadFile(finalM3Ufilename)
	if ((current_file is None) or (finalM3Ulist != current_file)):
		common.WriteFile(finalM3Ulist, finalM3Ufilename)
		UpdateIPTVSimpleSettings(iptvAddon, restart_pvr=True)
	else:
		UpdateIPTVSimpleSettings(iptvAddon, restart_pvr=False)
	# DeleteCache()
	
	common.ShowNotification("Updating is done.", 2000, addon=__Addon__)
	return True

def MakeM3U(list, is_logo_extension):
	M3Ulist = []
	M3Ulist.append("#EXTM3U\n")
	for item in list:
		tvg_logo = GetLogo(item.tvg_logo, is_logo_extension)
		M3Ulist.append('#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" group-title="{2}" tvg-logo="{3}",{4}\n{5}\n'.format(item.tvg_id.encode("utf-8"), item.tvg_name.encode("utf-8"), (item.group_title or "").encode("utf-8"), tvg_logo, item.channel_name.encode("utf-8"), item.url))
	return "\n".join(M3Ulist)

def DeleteCache():
	iptvsimple_path = __IPTVSimple__AddonDataPath____
	if (os.path.exists(iptvsimple_path)):
		for f in os.listdir(iptvsimple_path):
			if (os.path.isfile(os.path.join(iptvsimple_path,f))):
				if (f.endswith('cache')):
					os.remove(os.path.join(iptvsimple_path,f))

def UpdateIPTVSimpleSettings(iptvAddon = None, restart_pvr = False):
	if (iptvAddon is None):
		iptvAddon = GetIptvAddon()
		if (iptvAddon is None):
			return
	
	iptvSettingsFile = os.path.join(__IPTVSimple__AddonDataPath____, "settings.xml")
	if (not os.path.isfile(iptvSettingsFile)):
		iptvAddon.setSetting("epgPathType", "0") # make 'settings.xml' in 'userdata/addon_data/pvr.iptvsimple' folder
	
	# get settings.xml into dictionary
	settingsDictionary = ReadSettings(iptvSettingsFile, True)
	
	tempDictionary = {
		"epgPathType" : "0",
		"epgPath" : os.path.join(__AddonDataPath__, 'epg.xml'),
		"logoPathType" : "0",
		"logoPath" : os.path.join(__AddonDataPath__, 'logos'),
		"m3uPathType" : "0",
		"m3uPath" : os.path.join(__AddonDataPath__, 'iptv.m3u'),
	}
	
	isSettingsChanged = False
	for k, v in tempDictionary.iteritems():
		if ((settingsDictionary.has_key(k)) and (settingsDictionary[k] != v)):
			settingsDictionary[k] = v
			isSettingsChanged = True
		
	if (isSettingsChanged):
		WriteSettings(settingsDictionary, iptvSettingsFile)
	if (restart_pvr == True):
		xbmc.executebuiltin('StartPVRManager')

def ReadSettings(source, fromFile=False):
	tree = ET.parse(source) if fromFile else ET.fromstring(source)
	elements = tree.findall('*')

	settingsDictionary = {}
	for elem in elements:
		settingsDictionary[elem.get('id')] = elem.get('value')
	
	return settingsDictionary
	
def WriteSettings(settingsDictionary, iptvSettingsFile):
	xml = []
	xml.append("<settings>\n")
	for k, v in settingsDictionary.iteritems():
		xml.append('\t<setting id="{0}" value="{1}" />\n'.format(k, v))
	xml.append("</settings>\n")
	common.WriteFile("".join(xml), iptvSettingsFile)

def MakeEPG(epg_list):
	root = ET.Element("tv")
	for epg in epg_list:
		for channel in epg.channels:
			channel_element = ET.SubElement(root, "channel")
			channel_element.text = channel.display_name
			channel_element.set("id", channel.id)
	
			for program in channel.programs:
				program_element = ET.SubElement(root, "programme")
				program_element.set("start", program.start)
				program_element.set("stop", program.stop)
				program_element.set("channel", channel.id)
				
				ET.SubElement(program_element, "title").text = program.title
				if (program.subtitle is not None):
					ET.SubElement(program_element, "sub-title").text = program.subtitle
				if (program.description is not None):
					ET.SubElement(program_element, "desc").text = program.description
				if (program.category is not None):
					category_element = ET.SubElement(program_element, "category")
					category_element.text = program.category
					if (program.category_lang is not None):
						category_element.set("lang", program.category_lang)
				if ((program.credits is not None) and (len(program.credits) > 0)):
					credits_element = ET.SubElement(program_element, "credits")
					for credit in program.credits:
						job = credit.keys()[0]
						name = credit.values()[0]
						ET.SubElement(credits_element, job).text = name
			
			if ((program.length is not None) and (program.length_units is not None)):
				length_element = ET.SubElement(program_element, "length")
				length_element.text = program.length
				length_element.set("units", program.length_units)
			if (program.aspect_ratio is not None):
				ET.SubElement(ET.SubElement(program_element, "video"), "aspect").text = program.aspect_ratio
			if (program.star_rating is not None):
				ET.SubElement(ET.SubElement(program_element, "star-rating"), "value").text = program.star_rating
				
	epg_xml = '<?xml version="1.0" encoding="utf-8" ?>' + ET.tostring(root, encoding="utf-8")
	return epg_xml

def RefreshEPG(epg_list):
	if ((epg_list is not None) and (len(epg_list) > 0)):
		epgFile = os.path.join(__AddonDataPath__, 'epg.xml')
		restart_pvr = (not os.path.exists(epgFile))
		epg_xml = MakeEPG(epg_list)
		common.WriteFile(epg_xml, epgFile)
		if (restart_pvr):
			UpdateIPTVSimpleSettings(restart_pvr=True)

def GetLogo(link, is_logo_extension):
	if ((link is not None) and (len(link) > 4)):
		filename = link.split("/")[-1]
		ext = None
		if (filename > 4):
			ext =  filename[-4:].lower()
		if ((ext is None) or (ext != ".png")):
			filename = filename + ".png"
			link = link + ".png"
		
		full_filename = os.path.join(__AddonDataPath__, 'logos', filename)
		file_exists = (os.path.exists(full_filename) or common.DownloadFile(link, full_filename))
		
		if (file_exists):
			if (is_logo_extension):
				return filename
			else:
				return filename[:-4]
		else:
			return ""
	else:
		return ""

# -*- coding: utf-8 -*- 

import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import sys, os, urllib
import common
from xml.dom.minidom import parseString

URL_XML_FEED = 'http://www.annatel.tv/api/getchannels?login=%s&password=%s'
URL_EPG_FEED = 'http://xmltv.dtdns.net/alacarte/ddl?fichier=/xmltv_site/xmlPerso/arielus.zip'
__AddonID__ = 'plugin.video.annatel.tv'
__Addon__ = xbmcaddon.Addon(__AddonID__)
__AddonDataPath__ = os.path.join(xbmc.translatePath( "special://userdata/addon_data").decode("utf-8"), __AddonID__)
__XML__ = os.path.join(__AddonDataPath__, "Annatel", "XML")
__EPG__ = os.path.join(__AddonDataPath__, "Annatel", "EPG")

def GetCredentials():
	username = __Addon__.getSetting('username')
	password = __Addon__.getSetting('password')
	return (username, password)

def IsLoggedIn():
	username, password = GetCredentials()
	return ((username is not None) and (username != "") and (password is not None) and (password != ""))
		
def LoadLogin():
	resp = common.YesNoDialog("Authentification!",
							  "Il faut configurer votre login et mot de passe Annatel TV!",
							  "Cliquez sur Yes pour configurer votre login et mot de passe",
							  nolabel="Non",
							  yeslabel="Oui")
	if (resp):
		common.OpenSettings()
	else:
		common.ShowNotification("Authentification!\nMerci d\'entrer votre login et mot de passe Annatel TV", 10, addon=__Addon__)

def GetTVChannels():
	if (IsLoggedIn()):
		username, password = GetCredentials()
		xml_link = URL_XML_FEED % (urllib.quote(username), urllib.quote(password))
		local_xml = os.path.join(__XML__, "annatel.xml")
		doc = common.DownloadBinary(xml_link)
		if (doc is None):
			doc = common.ReadFile(local_xml)
		else:
			common.WriteFile(doc, local_xml)
			common.SetLastModifiedLocal(__XML__)
		
		if (doc is not None):
			response = []
			parsed_doc = parseString(doc)
			for channel in parsed_doc.getElementsByTagName('channel'):
				name = channel.getElementsByTagName('name')[0].childNodes[0].data
				url = channel.getElementsByTagName('url')[0].childNodes[0].data
				logo = channel.getElementsByTagName('logo')[0].childNodes[0].data
				tv_channel = common.TV(url, name, name, tvg_logo=logo)
				response.append(tv_channel)
			
			return response
		else:
			return None
	else:
		return None


def GetEPG():
	epg_xml = common.ReadZipUrl(URL_EPG_FEED, "arielus.xml", onDownloadFailed=EPGFailed, onDownloadSuccess=EPGSuccess)
	local_epg = os.path.join(__EPG__, "tvguide.xml")
	if (epg_xml is not None):
		common.WriteFile(epg_xml, local_epg)
		common.SetLastModifiedLocal(__EPG__)
	else:
		epg_xml = common.ReadFile(local_epg)
	
	if (epg_xml is not None):
		epg = ParseEPG(epg_xml)
		FixEPGChannelsIDs(epg)
		return epg
	else:
		return None

def EPGFailed():
	db_mod_time = common.GetLastModifiedFromDropBox("/EPG")
	local_mod_time = common.GetLastModifiedLocal(__EPG__)
	if ((db_mod_time is not None) and ((local_mod_time is None) or (db_mod_time > local_mod_time))):
		return common.DownloadDropBoxTempFile("/EPG", "tvguide.zip")
	else:
		return None

def EPGSuccess(zip_file):
	common.UploadDropBoxFile(zip_file, "/EPG", "tvguide.zip")
	common.SetLastModifiedToDropBox("/EPG")

def ParseEPG(epg_xml):
	epg = None
	if (epg_xml is not None):
		parsed_epg = parseString(epg_xml)
		epg = common.EPG()
		for channel in parsed_epg.getElementsByTagName('channel'):
			channel_id = channel.getAttribute("id").encode("utf-8")
			display_name = channel.getElementsByTagName('display-name')[0].childNodes[0].data.encode("utf-8")
			channel_epg = common.Channel(channel_id, display_name)
			epg.channels.append(channel_epg)
		
		current_channel = None
		for program in parsed_epg.getElementsByTagName('programme'):
			start = program.getAttribute("start")
			stop = program.getAttribute("stop")
			title = program.getElementsByTagName('title')[0].childNodes[0].data
			
			try:		subtitle = program.getElementsByTagName('sub-title')[0].childNodes[0].data
			except:		subtitle = None
			
			try:		description = program.getElementsByTagName('desc')[0].childNodes[0].data
			except:		description = None
			
			try:		aspect_ratio = program.getElementsByTagName("aspect")[0].childNodes[0].data
			except:		aspect_ratio = None
			
			try:		star_rating = program.getElementsByTagName("star-rating")[0].childNodes[0].childNodes[0].data # <star-rating><value>2/5</value></star-rating>
			except:		star_rating = None
			
			credits = []
			try:			
				for credit in program.getElementsByTagName('credits')[0].childNodes:
					job = credit.nodeName
					name = credit.childNodes[0].data
					credits.append({job:name})
			except:
				pass
			
			try:
				categoryNode = program.getElementsByTagName('category')[0]
				category = categoryNode.childNodes[0].data
				category_lang = categoryNode.getAttribute("lang")
			except:
				category = None
				category_lang = None
			
			try:
				lengthNode = program.getElementsByTagName('length')[0]
				length = lengthNode.childNodes[0].data
				length_units = lengthNode.getAttribute("units")
			except:
				length = None
				length_units = None
			
			program_epg = common.Program(start, stop, title)
			program_epg.subtitle = subtitle
			program_epg.description = description
			program_epg.credits = credits
			program_epg.category = category
			program_epg.category_lang = category_lang
			program_epg.length = length
			program_epg.length_units = length_units
			program_epg.aspect_ratio = aspect_ratio
			program_epg.star_rating = star_rating
			
			channel_id = program.getAttribute("channel")
			if ((current_channel is None) or (current_channel.id != channel_id)):
				current_channel = epg.GetChannelByID(channel_id)
			if (current_channel is not None):
				current_channel.programs.append(program_epg)
	
	return epg

def FixEPGChannelsIDs(epg):
	if (epg is not None):
		ids = {
			"1"	:	"TF1",
			"2"	:	"France_2",
			"3"	:	"France_3",
			"4"	:	"Canal_+",
			"5"	:	"France_5",
			"6"	:	"M6",
			"7"	:	"Arte",
			"8"	:	"D8",
			"9"	:	"W9",
			"10"	:	"TMC",
			"11"	:	"NT1",
			"12"	:	"NRJ_12",
			"13"	:	"France_4",
			"15"	:	"BFM_TV",
			#"16"	:	"i-télé",
			"16"	:	"i-tele",
			"17"	:	"D17",
			#"43"	:	"Canal+_Cinéma",
			"43"	:	"Canal+_Cinema",
			"45"	:	"Canal+_Family",
			"47"	:	"Canal+_Sport",
			"62"	:	"Cine+_Premier",
			"68"	:	"Comedie+",
			"74"	:	"Disney_Channel",
			"75"	:	"Disney_Cinema",
			"87"	:	"EuroNews",
			"89"	:	"EuroSport",
			"90"	:	"EuroSport2",
			"119"	:	"France_O",
			"168"	:	"National_Geo",
			"171"	:	"NickJr_France",
			"186"	:	"Paris_Première",
			"199"	:	"RTL9",
			#"227"	:	"Téva",
			"227"	:	"Teva",
			"288"	:	"France_24",
			#"4138"	:	"Canal+_Séries",
			"4138"	:	"Canal+_Series",
			"4139"	:	"BeIN_Sport_1_HD",
			"4140"	:	"BeIN_Sport_2_HD"
		}
		
		for channel in epg.channels:
			if (channel.id in ids):
				channel.id = ids[channel.id]


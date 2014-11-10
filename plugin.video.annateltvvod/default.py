import xbmcaddon, xbmcgui, xbmcplugin
import sys, os, urllib
from xml.dom.minidom import parse

URL_XML_FEED = 'http://www.annatel.tv/api/xbmc/vod/date'

__settings__ = xbmcaddon.Addon(id='plugin.video.annateltvvod')
__language__ = __settings__.getLocalizedString


username = __settings__.getSetting('username')
password = __settings__.getSetting('password')

LNK_PATH = os.path.join(__settings__.getAddonInfo('path'), 'resources','box.lnk')

class AnnatelTVVod:
    """
    main plugin class
    """
    debug_mode = True # Debug mode
    
    def __init__( self, *args, **kwargs ):
        params  = self.get_params()
        channel     = None
        date    = None
        mode    = None            
        try:
            channel=urllib.unquote_plus(params["channel"])
        except:
            pass
        try:
            date=urllib.unquote_plus(params["date"])
        except:
            pass
        try:
            mode=int(params["mode"])
        except:
            pass
		
        if self.debug_mode:
            print "Mode: "+str(mode)
            print "Channel: "+str(channel)
            print "Date: "+str(date)
			
        if mode==None or channel==None or len(channel)<1:
            self.GET_CHANNELS()
            xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=__language__ ( 30000 ) )
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        elif mode == 2:
            self.GET_DATES(channel)
            xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=__language__ ( 30000 ) )
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        elif mode == 3:
            self.GET_PROGRAMS(channel,date)
            xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=__language__ ( 30000 ) )
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )



    def GET_CHANNELS(self):
		URL = URL_XML_FEED+'?login='+urllib.quote(__settings__.getSetting('username'))+'&password='+urllib.quote(__settings__.getSetting('password'))
		doc = parse(urllib.urlopen(URL))
		for channel in doc.getElementsByTagName('channel') :
			name = channel.getElementsByTagName('name')[0].childNodes[0].data
			stream = channel.getElementsByTagName('stream')[0].childNodes[0].data			
			self.addDir(name,stream,"",2,"")  
		
		
    def GET_DATES(self,channel):
		URL = URL_XML_FEED+'?login='+urllib.quote(__settings__.getSetting('username'))+'&password='+urllib.quote(__settings__.getSetting('password'))+'&act=channel&channel='+urllib.quote(channel)
		doc = parse(urllib.urlopen(URL))
		for i in doc.getElementsByTagName('date') :
			name = i.getElementsByTagName('display')[0].childNodes[0].data
			day = i.getElementsByTagName('day')[0].childNodes[0].data			
			self.addDir(name,channel,day,3,"") 
			
    def GET_PROGRAMS(self,channel,date):
		URL = URL_XML_FEED+'?login='+urllib.quote(__settings__.getSetting('username'))+'&password='+urllib.quote(__settings__.getSetting('password'))+'&act=program&channel='+urllib.quote(channel)+'&day='+urllib.quote(date)
		doc = parse(urllib.urlopen(URL))
		for p in doc.getElementsByTagName('program') :
			name = p.getElementsByTagName('name')[0].childNodes[0].data
			uri = p.getElementsByTagName('url')[0].childNodes[0].data	
			description = p.getElementsByTagName('description')[0].childNodes[0].data	
			info = {"Title": name,"Label": name, "Plot": description}
			
			liz=xbmcgui.ListItem(name,name, iconImage="DefaultVideo.png")
			liz.setInfo(type="Video", infoLabels=info)
			liz.setProperty('IsPlayable', 'true')
			xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=uri,listitem=liz)			
		
        
    def addLink(self,name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok         

    def addDir(self,name,channel,date,mode,iconimage):
        u=sys.argv[0]+"?channel="+urllib.quote_plus(channel)+"&mode="+str(mode)+"&date="+urllib.quote_plus(date)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
    
    def get_params(self):
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param

    def get_soup(self,url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 5.1; rv:15.0) Gecko/20100101 Firefox/15.0.1')           
        soup = urllib2.urlopen(req).read()
        if (self.debug_mode):
            print str(soup)
        return soup   
                                       

if __name__ == '__main__' :
	if username == '' or password == '':
		resp = xbmcgui.Dialog().yesno("Authentification","Il faut configurer votre login et mot de passe Annatel TV!\nCliquez sur Yes pour configurer votre login et mot de passe")
		if resp:
			respLogin = __settings__.openSettings()
			if respLogin:
				username = __settings__.getSetting('username')
				password = __settings__.getSetting('password')
			else:
				xbmc.executebuiltin('XBMC.Notification("Authentification","Merci d\'entrer votre login et mot de passe Annatel TV", 5000)')				
		else:
			xbmc.executebuiltin('XBMC.Notification("Authentification","Merci d\'entrer votre login et mot de passe Annatel TV", 10000)')

	username = __settings__.getSetting('username')
	password = __settings__.getSetting('password')
	if username != '' and password != '':
		AnnatelTVVod()
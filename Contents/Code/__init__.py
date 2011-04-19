import urllib
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

TITLE				= "Demand Five"
PLUGIN_PREFIX   	= "/video/fivetv"
ROOT            	= "http://demand.five.tv"
SHOW_URL			= "%s/Series.aspx?seriesBaseName=" % ROOT
EPISODE_URL			= "%s/Episode.aspx?episodeBaseName=" % ROOT
A_Z					= "%s/seriesAZ.aspx" % ROOT
WATCH_NOW			= "%s/WatchNow.aspx" % ROOT
SEARCH				= "%s/searchresults.aspx?search=" % ROOT
FEED_LAST_NIGHT		= "%s/Handlers/LastNightRssFeed.ashx" % ROOT
FEED_NEW			= "%s/Handlers/NewRssFeed.ashx" % ROOT
FEED_POPULAR		= "%s/Handlers/PopularRssFeed.ashx" % ROOT
FEED_RECOMMENDED	= "%s/Handlers/RecommendedRssFeed.ashx" % ROOT

####################################################################################################
def Start():
  # Add the MainMenu prefix handler
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, L(TITLE))
  
  # Set up view groups
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Info", viewMode="InfoList", mediaType="items")
  
  # Set the default cache time
  HTTP.SetCacheTime(14400)
  
  # Set the default MediaContainer attributes
  MediaContainer.title1 = L(TITLE)
  MediaContainer.viewGroup = "List"
  MediaContainer.art = R("art-default.png")

####################################################################################################

def CreateDict():
  # Create dict objects
  Dict.Set("shows", {})
  Dict.Set("episodes", {})

####################################################################################################
  
def UpdateCache():

	# Store the cached data

	shouldSave = False
	# Fetch all show pages & store the metadata
	Log("Fetching show pages")

	shows = Dict.Get("shows")
	
	for rows in XML.ElementFromURL(A_Z, True).xpath("//table[@class='episodeTable']/tr"):
		for column in rows.xpath('td'):
			thumb = column.xpath('a/img')[0].get('src')
			thumb = getBigImage(thumb)

			showId = getId(column.xpath('span/a')[0].get('href'))
			title = column.xpath('span/a')[0].text

			if showId not in shows and checkShowPlayability(showId):
				
				try:
					summary = unicode(XML.ElementFromURL(SHOW_URL + showId, True).xpath("//div[@class='promocontent']")[0].text.strip())
				except:
					summary = ""
					print "Error handling summary"
					
				shows[showId] = Show(title,thumb,showId,summary)
				
				CacheEpisodes(showId, title, 1296000)
				shouldSave = True

	if shouldSave:
		Dict.Set("shows",shows)

####################################################################################################

def CacheEpisodes(show, showTitle, cacheTime=None):
	data = XML.ElementFromURL(SHOW_URL + show, True).xpath("//div[@class='episodesOff']")
	
	# Get a list in descening order
	data.reverse()

	shouldSave = False
	shows = Dict.Get("shows")
	episodes = Dict.Get("episodes")

	for result in data:
		episode = Episode(result,showTitle)
		
		if episode.episodeId not in episodes:
			episodes[episode.episodeId] = episode
			shouldSave = True
	
	if shouldSave:
		Dict.Set("episodes",episodes)
	

####################################################################################################

def MainMenu():
	dir = MediaContainer()
	dir.Append(Function(DirectoryItem(AtoZ, title=L("Programmes A to Z"))))
#	dir.Append(Function(DirectoryItem(Feeds, title=L("Last Night on Five")),feed=FEED_LAST_NIGHT))
	dir.Append(Function(DirectoryItem(Feeds, title=L("New on Demand Five")),feed=FEED_NEW))
	dir.Append(Function(DirectoryItem(Feeds, title=L("Popular on Demand Five")),feed=FEED_POPULAR))
	dir.Append(Function(DirectoryItem(Feeds, title=L("Recommended by Demand Five")),feed=FEED_RECOMMENDED))
	dir.Append(Function(DirectoryItem(Genre, title=L("Genres"))))
	dir.Append(Function(SearchDirectoryItem(Search,"search", L("SearchItem"), L("SearchPrompt"))))
	return dir

####################################################################################################

def Search(sender,query):
	dir = MediaContainer(title2=L("SEARCH"))
	
	page = XML.ElementFromURL(SEARCH + query, True)

	shows = Dict.Get("shows")

	for show in page.xpath("//div[@class='serTxt']/span/a"):
		try:
			showId = getId(show.get('href'))
			if showId in shows:
				shows[showId].append(dir,query)
		except:
			Log("Error loading show")

	episodes = Dict.Get("episodes")

	for episode in page.xpath("//div[@class='episodeReslt']/a"):
		#try:
		episodeId = getId(episode.get('href'))
		if episodeId in episodes:
			episodes[episodeId].append(dir,detail=1)
			
	return dir

####################################################################################################

def AtoZ(sender):

	dir = MediaContainer(title2=L("A to Z"))

	shows = Dict.Get("shows")

	for rows in XML.ElementFromURL(A_Z, True).xpath("//table[@class='episodeTable']/tr"):
		for column in rows.xpath('td'):
			showId = getId(column.xpath('span/a')[0].get('href'))
			
			if showId in shows:
				shows[showId].append(dir,"A to Z")
			
	return dir

####################################################################################################

def Feeds(sender,feed):
	dir = MediaContainer(title2=L(sender.itemTitle))

	episodes = Dict.Get("episodes")
	shows = Dict.Get("shows")

	for item in XML.ElementFromURL(feed, True).xpath("//item"):
		
		identifier = getId(item.xpath("guid")[0].text)
		
		if feed == FEED_LAST_NIGHT:
			if identifier in episodes:
				episodes[identifier].append(dir)
		else:
			atoms = identifier.split("Season")
			if len(atoms) > 1:
				identifier = atoms[0]
				
			if identifier in shows:
				shows[identifier].append(dir)
	
	return dir

####################################################################################################

def Genre(sender,genre=""):
	if genre == "":
		dir = MediaContainer(title2=L("Genre"))
		dir.Append(Function(DirectoryItem(Genre, title=L("Entertainment")),genre="entertainment"))
		dir.Append(Function(DirectoryItem(Genre, title=L("Drama")),genre="drama"))
		dir.Append(Function(DirectoryItem(Genre, title=L("Documentary")),genre="documentary"))
		dir.Append(Function(DirectoryItem(Genre, title=L("Soap")),genre="soap"))
		dir.Append(Function(DirectoryItem(Genre, title=L("Milkshake!")),genre="milkshake!"))
	else:
		dir = MediaContainer(title1=L("Genre"),title2=L(genre))

		shows = Dict.Get("shows")

		for genres in XML.ElementFromURL(WATCH_NOW, True).xpath("//div[@class='showList']"):
			
			if genres.xpath("div[@class='header']")[0].text == "all " + str(genre):
				for show in genres.xpath("div/div/ul/li/a"):
					showId = getId(show.get('href'))

					if showId in shows:
						shows[showId].append(dir,genre)

	return dir

####################################################################################################

def ListShow(sender,showId,title2):

	shows = Dict.Get("shows")
	show = shows[showId]

	dir = MediaContainer(title1=title2, title2=show.title, viewGroup="Info")
		
	data = XML.ElementFromURL(SHOW_URL + str(showId), True).xpath("//div[@class='episodesOff']")
		
	# Get a list in descening order
	data.reverse()
	
	episodes = Dict.Get("episodes")
	
	for result in data:
		episode = Episode(result,title2)
		if episode.episodeId in episodes:
			episode.append(dir)

	return dir

####################################################################################################

def checkShowPlayability(showId):
 	episodeUrl = XML.ElementFromURL(SHOW_URL + showId, True).xpath("//a[@id='ctl00_MainContent_SFELatest_lnkHeader']")
 	
 	if len(episodeUrl) > 0:
 		episodeUrl = getId(episodeUrl[0].get('href'))
 	else:
 		Log("Error: " + showId)
	
	return checkEpisodePlayability(episodeUrl)

####################################################################################################

def checkEpisodePlayability(episodeId):

	if len(XML.ElementFromURL(EPISODE_URL + str(episodeId), True).xpath("//div[@id='flashPlayer']")) > 0:
		return True
	else:
		return False

####################################################################################################

def getBigImage(image):
	return image.replace("Small.png","Big.jpg")

####################################################################################################

def getId(url):
	atoms = str(url).split("=")
	
	return atoms[len(atoms)-1]

####################################################################################################

class Episode:
	title = ""
	subtitle = ""
	thumb = ""
	episodeId = ""
	summary = ""
	showTitle = ""
	duration = 0

	def __init__(self,data,showTitle):
		# Show Title
		self.showTitle = showTitle
	
		# Title
		links = data.xpath("div/div/a")
		title1 = links[2].text.capitalize().strip().replace(" :","")
		title2 = links[3].text.strip()
			
		if title1 != title2:
			self.title = title1 + str(": ") + title2
		else:
			self.title = title1
			
		# URL
		if len(links) > 4:
			self.episodeId = getId(links[4].get('href'))

		# Duration
		try:
			self.duration = data.xpath("div/div/div")[1].text.split(" ")[0].strip()
		except:
			print "Error handling summary"

		try:
			thumb = data.xpath("div[@class='epimoreinfo']/div/img")[0].get("src")
			self.thumb = getBigImage(thumb)
		except:
			pass

		temp = data.xpath("div/div")
		try:
			if len(temp) > 4:
				self.summary = unicode(temp[4].text.strip())
		except:
			pass
			
		if self.duration > 0:
			self.summary += "\n\n" + self.duration + " minutes"

	def getUrl(self):
		return EPISODE_URL + self.episodeId

	def append(self,dir,detail=0):
		if self.episodeId != "":
		
			if detail == 0 or self.showTitle == "":
				t = self.title
			else:
				t = self.showTitle + " - " + self.title
		
			item = WebVideoItem(self.getUrl(), title=t, subtitle=self.subtitle, summary=self.summary, thumb=self.thumb)
			dir.Append(item)

####################################################################################################

class Show:
	title = ""
	thumb = ""
	showId = ""
	summary = ""

	def __init__(self,title,thumb,showId,summary=""):
		self.title = title
		self.thumb = thumb
		self.showId = showId
		self.summary = summary
	
	def getUrl(self):
		return SHOW_URL + self.showId
	
	def append(self,dir,title2=""):
		dir.Append(Function(DirectoryItem(ListShow, title=L(self.title), thumb=self.thumb),showId=self.showId,title2=title2))

		#urllib.quote()

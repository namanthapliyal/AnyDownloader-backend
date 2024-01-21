from pytube import YouTube
from pytube import Playlist
from pytube import Channel

class dVideo():
    def __init__(self, url):
        self.yt=YouTube(url)
        self.ITag=None
        self.caption=None
        self.lang=None

    def getTitle(self):
        try:
            return [True, self.yt.title]
        except Exception as e:
            print(e)
            return [False, e]
    
    def getCaptions(self):
        try:
            self.yt.streams.first()
            return [True, self.yt.captions]
        except Exception as e:
            print(e)
            return [False, e]

    def setCaptionLang(self, lang):
        self.capLang=lang
        return [True, self.capLang]

    def downloadCaptions(self):
        try:
            return [True, self.caption[self.capLang].download(self.title)]
        except Exception as e:
            print(e)
            return [False, e]
    
    def getStreams(self):
        try:   
            return [True, self.yt.streams]
        except Exception as e:
            print(e)
            return [False, e] 

    def setITag(self, itag):
        try:
            self.ITag=self.yt.streams.get_by_itag(itag)
            return [True, self.ITag]
        except Exception as e:
            print(e)
            return [False, e] 

    def download(self):
        try:
            self.itag.download()
            return [True, None]
        except Exception as e:
            print(e)
            return [False, e] 

class dPlaylist():
    def __init__(self, url):
        self.p=Playlist(url)
        self.title=self.p.title
        self.res=None

    def getTitle(self):
        try:
            return [True, self.p.title]
        except Exception as e:
            print(e)
            return [False, e]
    
    def getQuality(self):
        try:
            quality=[]
            for i in self.p.videos:
                quality.append(i.streams[0].resolution)
            return [True, quality]
        except Exception as e:
            print(e)
            return [False, e]

    def setQuality(self, res):
        self.res=res
        return [True, self.res]

    def downloadVideos(self):
        try:
            for i in self.p.videos:
                itag=i.streams.filter(progressive=True, res=self.res)
                video=i.streams.get_by_itag()
                video.download()
            return [True, None]
        except Exception as e:
            print("Error: {}".format(e))
            return [False, e]

# class dChannel():
#     def __init__(self, url) -> None:
#         self.c=Channel(url)
#         self.cName=self.c.channel_name
#         self.res=None
    
#     def getChannelName(self):
#         return self.cName
    





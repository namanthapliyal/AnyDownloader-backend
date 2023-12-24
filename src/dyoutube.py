from pytube import YouTube
from pytube import Playlist
from pytube import Channel

class dVideo():
    def __init__(self, url):
        self.yt=YouTube(url)
        self.title=self.yt.title
        self.audioTag=None
        self.videoTag=None
        self.caption=None
        self.lang=None

    def getTitle(self):
        return self.title
    
    def getCaptions(self):
        self.yt.streams.first()
        return self.yt.captions

    def setCaptionLang(self, lang):
        self.capLang=lang

    def downloadCaptions(self):
        return self.caption['self.capLang'].download(self.title)
    
    def getStreams(self):
        return self.yt.streams

    def setAudioTag(self, itag):
        self.audioTag=self.yt.streams.get_by_itag(itag)
    
    def setVideoTag(self, itag):
        self.videoTag=self.yt.streams.get_by_itag(itag)

    def download(self, itag):
        return itag.download()

class dPlaylist():
    def __init__(self, url):
        self.p=Playlist(url)
        self.title=self.p.title
        self.res=None

    def getTitle(self):
        return self.title
    
    def setQuality(self):
        quality=[]
        for i in self.p.videos:
            quality.append(i.streams[0].resolution)
        return quality

    def setQuality(self, res):
        self.res=res

    def downloadVideos(self):
        try:
            for i in self.p.videos:
                itag=i.streams.filter(progressive=True, res=self.res)
                video=i.streams.get_by_itag()
                video.download()
        except Exception as e:
            print("Error: {}".format(e))

# class dChannel():
#     def __init__(self, url) -> None:
#         self.c=Channel(url)
#         self.cName=self.c.channel_name
#         self.res=None
    
#     def getChannelName(self):
#         return self.cName
    





import instagrapi
import requests

class dInstagram():
    def __init__(self, postUrl=None, username=None, password=None):
        self.username=username
        self.insta=instagrapi.Client()
        self.password=password
        self.postUrl=postUrl
        self.id=None
    
    def setUrl(self, url):
        self.postUrl=url

    def getContentType(self, url):
        res=requests.get(url)
        if res.content:
            return res.headers['Content-Type']
        else:
            return res.status_code

    def login(self):
        try:
            self.insta.login(self.username, self.password)
        except Exception as e:
            print(e)
            return e

    def getId(self):
        try:
            self.id=self.insta.media_pk_from_url(self.postUrl)
            return self.id
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return e
        except Exception as e:
            print("Unexpected error:", e)
            return e

    def getResources(self):
        try:
            self.getId()
            resources=self.insta.media_info(self.id).resources
            return resources
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return e
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return e

    def mediaType(self):
        try:
            self.getId()
            mtype=self.insta.media_info(self.id).media_type
            if mtype==1:
                return "Photo"
            elif mtype==2:
                if self.insta.media_info(self.id).product_type=="feed":
                    return "Video"
                elif self.insta.media_info(self.id).product_type=="igtv":
                    return "IGTV"
                elif self.insta.media_info(self.id).product_type=="clips":
                    return "Clips"
            elif mtype==8:
                return "Album"
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return e
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return e

    def save(self, url, id):
        contentType=self.getContentType(url)
        filename=self.insta.media_info(id).id+'.'+contentType.split('/')[1]
        res=requests.get(url)
        with open(filename, "wb") as f:
            f.write(res.content)

    def download(self):
        try:
            type=self.mediaType()
            if type=="Photo":
                url=self.insta.media_info(self.id).thumbnail_url
                self.save(url, self.id)
            elif type=="Video":
                url=self.insta.media_info(self.id).video_url
                self.save(url, self.id)
            elif type=="Album":
                resources=self.getResources()
                for r in resources:
                    url=r.thumbnail_url
                    id=r.pk
                    self.save(url, id)
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return e
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return e

    # def downloaderFromHashtags(self, hastag, since, until):
    #     posts=self.insta.Hashtag.from_name(self.insta.context, hastag).get_posts()
    #     since = datetime(since)  # further from today, inclusive
    #     until = datetime(until)  # closer to today, not inclusive
        

import instagrapi
import requests

class dInstagram():
    def __init__(self, userId, username=None, password=None):
        self.username=username
        self.insta=instagrapi.client()
        self.password=password
        self.userId=userId
    
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

    def getResourceId(self, url):
        try:
            return self.insta.media_pk_url(url)
        except Exception as e:
            print("Error: {} trying after logging in.")

    def getContentUrl(self, url):
        self.insta

    def downloadPost(self, url):
        
    
    def downloadProfile():
        pass

    def downloadStory():
        pass

    def downloadIgtv():
        pass

    def instaLogin(self, user, password):
        self.insta.login(user, password)

    def downloaderFromHashtags(self, hastag, since, until):
        posts=self.insta.Hashtag.from_name(self.insta.context, hastag).get_posts()
        since = datetime(since)  # further from today, inclusive
        until = datetime(until)  # closer to today, not inclusive
        

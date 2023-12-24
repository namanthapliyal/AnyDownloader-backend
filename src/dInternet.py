import requests
import mimetypes

class dInternet():
    def __init__(self, url):
        self.url=url
        self.mime=mimetypes.guess_type(self.url)

    def getType(self):
        return self.mime[0].split('/')[0]
    
    def getExt(self):
        return self.mime[0].split('/')[1]
    
    def download(self, filename='download'):
        response=requests.get(self.url)
        filename+='.{}'.format(self.getExt)
        if response.status_code==200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return response.status_code
        else:
            return response.status_code

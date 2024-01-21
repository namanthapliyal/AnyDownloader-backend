import requests
import mimetypes

class dInternet():
    def __init__(self, url):
        self.url=url

    def getType(self):
        try:
            mime = mimetypes.guess_type(self.url)
            return [True, mime[0].split('/')[0]]
        except Exception as e:
            return [False, e]
        
    def getExt(self):
        try:
            mime = mimetypes.guess_type(self.url)
            return [True, mime[0].split('/')[1]]
        except Exception as e:
            return [False, e]
    
    def download(self, filename='download'):
        try:
            status, res = self.getExt()
            if status:
                response=requests.get(self.url)
                filename+='.{}'.format(res)
                if response.status_code==200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    return [True, "File saved into "+filename]
                else:
                    raise Exception("Cannot get the resonse for the supplied URL.")
            else:
                raise Exception("Unable to get the extension for the file.")
        except Exception as e:
            print(e)
            return [False, e]

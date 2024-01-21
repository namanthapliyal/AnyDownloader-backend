import instagrapi
import requests

class dInstagram():
    def __init__(self, postUrl=None, username=None, password=None):
        self.username=username
        self.insta=instagrapi.Client()
        self.password=password
        self.postUrl=postUrl
        self.id=None
    
    #main
    def setUrl(self, url):
        self.postUrl=url
        return [True, None]

    def getContentType(self, url):
        res=requests.get(url)
        if res.content:
            return [True, res.headers['Content-Type']]
        else:
            return [False, res.status_code]

    def setUserandPass(self, username, password):
        self.username=username
        self.password=password
        return [True, None]

    #main
    def login(self, username, password):
        try:
            self.setUserandPass(username, password)
            self.insta.login(self.username, self.password)
            return [True, None]
        except Exception as e:
            print(e)
            return [False, e]

    def getId(self):
        try:
            self.id=self.insta.media_pk_from_url(self.postUrl)
            return [True, self.id]
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print("Unexpected error:", e)
            return [False, e]

    def getResources(self):
        try:
            status, id = self.getId()
            if(status):
                resources=self.insta.media_info(self.id).resources
                return [True, resources]
            else:
                raise Exception("Setting of the resource id failed.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]

    def mediaType(self):
        try:
            status, id = self.getId()
            if(status):
                mtype=self.insta.media_info(self.id).media_type
                if mtype==1:
                    return [True, "Photo"]
                elif mtype==2:
                    if self.insta.media_info(self.id).product_type=="feed":
                        return [True, "Video"]
                    elif self.insta.media_info(self.id).product_type=="igtv":
                        return [True, "IGTV"]
                    elif self.insta.media_info(self.id).product_type=="clips":
                        return [True, "Clips"]
                elif mtype==8:
                    return [True, "Album"]
            else:
                raise Exception("Failed to set the resource id.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]

    def save(self, url, id):
        try:
            status, contentType=self.getContentType(url)
            if(status):
                filename=self.insta.media_info(id).id+'.'+contentType.split('/')[1]
                res=requests.get(url)
                with open(filename, "wb") as f:
                    f.write(res.content)
                return [True, "File saved at: "+filename]
            else:
                raise Exception("URL is not valid or doesn't contain a file.")
        except Exception as e:
            print(e)
            return [False, e]

    #main
    def download(self):
        try:
            status, type=self.mediaType()
            res=None
            if(status):
                if type=="Photo":
                    url=self.insta.media_info(self.id).thumbnail_url
                    status2, res= self.save(url, self.id)
                    if(status2):
                        print("Download photo success!")
                    else:
                        print("Download failed.")
                        raise Exception("Download failed.")
                elif type=="Video":
                    url=self.insta.media_info(self.id).video_url
                    status2, res= self.save(url, self.id)
                    if(status2):
                        print("Download video success!")
                    else:
                        print("Download failed.")
                        raise Exception("Download failed.")
                elif type=="Album":
                    status, resources=self.getResources()
                    if(status):
                        res=[]
                        for r in resources:
                            url=r.thumbnail_url
                            id=r.pk
                            status2, tmp= self.save(url, id)
                            if(status2):
                                res.append(tmp)
                                print("Url: "+url+" saved.")
                            else:
                                print("Url: "+url+" not saved.")
                        if(len(res)!=len(resources) and len(res)>0):
                            print("Not all files in Album are downloaded.")
                        else:
                            raise Exception("Not all files in Album are downloaded.")
                    else:
                        raise Exception("No resources found in the album.")
                return [True, res]
            else:
                raise Exception("Failed to load the type of the resource.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]

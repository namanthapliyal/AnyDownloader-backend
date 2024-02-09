from flask import Blueprint, request, jsonify
from .models import obj_table, media
import instagrapi
import requests
from . import db 
import os

download_path = os.path.join(os.getcwd(), 'downloads')

class dInstagram():
    def __init__(self, postUrl, username=None, password=None):
        self.username=username
        self.insta=instagrapi.Client()
        self.password=password
        self.postUrl=postUrl
        self.id=None

    def getContentType(self, url):
        res=requests.get(url)
        if res.content:
            return [True, res.headers['Content-Type']]
        else:
            return [False, res.status_code]

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
                resources=self.insta.media_info(id).resources
                print(resources)
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
                mtype=self.insta.media_info(id).media_type
                if mtype==1:
                    return [True, "Photo"]
                elif mtype==2:
                    if self.insta.media_info(id).product_type=="feed":
                        return [True, "Video"]
                    elif self.insta.media_info(id).product_type=="igtv":
                        return [True, "IGTV"]
                    elif self.insta.media_info(id).product_type=="clips":
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
                filepath=download_path
                full_path = os.path.join(filepath, filename)
                print("filepath ye ra:{}".format(full_path))
                res=requests.get(url)
                with open(full_path, "wb") as f:
                    f.write(res.content)
                med = media(media_path=full_path, resource_id=id)
                db.session.add(med)
                db.session.commit()
                return [True, "File saved at: "+full_path]
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
                elif type=="Clips":
                    url=self.insta.media_info(self.id).video_url
                    status2, res= self.save(url, self.id)
                    if(status2):
                        print("Download clips success!")
                    else:
                        print("Download failed.")
                        raise Exception("Download failed.")
                return [True, res]
            else:
                raise Exception("Failed to load the type of the resource.")
        except instagrapi.exceptions.LoginRequired as e:
            print("Error: {} trying after logging in.".format(e))
            return [False, e]
        except Exception as e:
            print('Failed to fetch media info with error :',str(e))
            return [False, e]


insta_views = Blueprint('insta_views', __name__)

@insta_views.route('/', methods=['POST'])
def create_obj():
    try:
        url = request.form.get('url')
        obj = obj_table(url=url)
        if request.form.get('username', 0):
            obj.username = request.form.get('username')
        if request.form.get('password', 0):
            obj.password = request.form.get('password')
        db.session.add(obj)
        db.session.commit()
        return jsonify({"messages": "Initialized state of the object.", "id": obj.id})
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@insta_views.route('/login/<int:id>', methods=['PATCH'])   
def login(id):
    try:
        obj = obj_table.query.get(id)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        username = request.form.get('username')
        password = request.form.get('password')
        status, res = ins.login(username=username, password=password)
        if not status:
            return jsonify({"messages": res}), 401
        obj.username = username
        obj.password = password
        db.session.commit()
        return jsonify({"messages": "Login successful."}), 200   
    except Exception as e:
        return jsonify({"messages": e}), 500

@insta_views.route('/<int:id>/resources', methods=['GET'])
def getResources(id):
    try:
        obj = obj_table.query.get(id)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.getResources()
        print(status, res)
        if status:
            return jsonify(res), 200
        else:
            return jsonify({"messages": res}), 500
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@insta_views.route('/<int:id>/getmediatype', methods=['GET'])
def getMediaType(id):
    try:
        obj = obj_table.query.get(id)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.mediaType()
        if status:
            return jsonify(res), 200
        else:
            return jsonify({"messages": res}), 500
    except Exception as e:
        return jsonify({"messages": e}), 500

@insta_views.route('/<int:id>/download') 
def download(id):
    try:
        obj = obj_table.query.get(id)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.download()
        if status:
            return jsonify({"messages": res}), 201
        else:
            return jsonify({"messages": str(res)}), 500
    except Exception as e:
        return jsonify({"messages": e}), 500


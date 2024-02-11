from flask import Blueprint, request, jsonify, send_file
from .models import obj_table, media
import instagrapi
import requests
from . import db 
import os
import zipfile

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
            self.username=username
            self.password=password
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
        def serialize_resource(resource):
            return resource.json()
        try:
            status, id = self.getId()
            if(status):
                resources=self.insta.media_info(id).resources
                res = [serialize_resource(resource) for resource in resources]
                return [True, res]
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
                med = media(media_path=full_path, resource_id=id, rtype=self.mediaType()[1])
                db.session.add(med)
                db.session.commit()
                return [True, full_path]
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
                    print(resources[0])
                    print("ye ra type:{}".format(type(resources[0])))
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
                        zip_file_path = os.path.join(download_path, 'download{}.zip'.format(self.id))
                        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                            for file_path in res:
                                # Get only the filename from the file_path
                                file_name = os.path.basename(file_path)
                                # Add the file to the ZIP file without any directory structure
                                zipf.write(file_path, arcname=file_name)
                        res=zip_file_path
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
                    print(res)
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
        obj = obj_table.query.filter_by(url=url).first()
        if obj:
            return jsonify({'messages': 'Object already present in db.', "id": obj.id})
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
        ins = dInstagram(postUrl=obj.url)
        username = request.form.get('username')
        password = request.form.get('password')
        status, res = ins.login(username=username, password=password)
        if not status:
            return jsonify({"messages": str(res)}), 401
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
        if status:
            return jsonify(res), 200
        else:
            return jsonify({"messages": str(res)}), 500
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
            return jsonify({"messages": str(res)}), 500
    except Exception as e:
        return jsonify({"messages": str(e)}), 500

@insta_views.route('/<int:id>/download') 
def download(id):
    try:
        obj = obj_table.query.get(id)
        mobj = media.query.filter_by(resource_id=obj.id).first()
        if mobj and os.path.exists(mobj.media_path):
            print("Media already exists.")
            return send_file(mobj.media_path, as_attachment=True)
        ins = dInstagram(postUrl=obj.url, username=obj.username, password=obj.password)
        status, res = ins.download()
        if status:
            med = media(media_path=res, resource_id=id)
            db.session.add(med)
            db.session.commit()  
            return send_file(res, as_attachment=True)
        else:
            return jsonify({"messages": str(res)}), 500
    except Exception as e:
        return jsonify({"messages": e}), 500


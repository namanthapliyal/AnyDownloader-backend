import requests
import mimetypes
from flask import Blueprint, request, jsonify, send_file
from . import db 
from .models import obj_table, media
import os

download_path = os.path.join(os.getcwd(), 'downloads')

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
    
    def download(self, id, filename='download'):
        try:
            status, res = self.getExt()
            if status:
                response=requests.get(self.url)
                filepath = os.path.join(download_path, '{}.{}'.format(filename+str(id), res))
                if response.status_code==200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    return [True, filepath]
                else:
                    raise Exception("Cannot get the resonse for the supplied URL.")
            else:
                raise Exception("Unable to get the extension for the file.")
        except Exception as e:
            print(e)
            return [False, e]
        
internet_views = Blueprint('internet_views', __name__)

@internet_views.route('/', methods=['POST'])
def create_url():
    try:
        url = request.form.get('url')
        obj = obj_table.query.filter_by(url=url).first()
        if obj:
            return jsonify({'messages': 'Object already present in db.', "id": obj.id})
        obj = obj_table(url=url)
        db.session.add(obj)
        db.session.commit()
        return jsonify({"messages": "Initialized state of the object.", "id": obj.id})
    except Exception as e:
        return jsonify({"messages": e}), 500

@internet_views.route('/<int:id>/download', methods=['GET'])
def download(id):
    try:
        obj = obj_table.query.get(id)
        internet = dInternet(obj.url)
        mobj = media.query.filter_by(resource_id=obj.id).first()
        if mobj and os.path.exists(mobj.media_path):
            print("Media already exists.")
            return send_file(mobj.media_path, as_attachment=True)
        status, res = internet.download(id=id)
        if status:
            med = media(media_path=res, resource_id=id, rtype=internet.getType()[1])
            db.session.add(med)
            db.session.commit()            
            return send_file(res, as_attachment=True)
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": str(e)}), 500
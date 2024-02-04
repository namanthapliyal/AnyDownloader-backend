import requests
import mimetypes
from flask import Blueprint, request, jsonify
from . import db 
from .models import obj_table

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
        
internet_views = Blueprint('internet_views', __name__)

@internet_views.route('/', methods=['POST'])
def create_url():
    try:
        url = request.form.get('url')
        obj = obj_table(url=url)
        db.session.add(obj)
        db.session.commit()
        return jsonify({"messages": "Initialized state of the object.", "id": obj.id})
    except Exception as e:
        return jsonify({"messages": e}), 500

@internet_views.route('/<int:id>/download', methods=['GET'])
def download():
    try:
        obj = obj_table.query.get(id)
        internet = dInternet(obj.url)
        status, res = internet.download()
        if status:
            return jsonify({"messages": res}), 200
        else:
            raise Exception(e)
    except Exception as e:
        return jsonify({"messages": e}), 500
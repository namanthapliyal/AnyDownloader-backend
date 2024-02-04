from pytube import YouTube
from pytube import Playlist
from pytube import Channel
from flask import Blueprint, request, jsonify, send_file
from . import db 
from .models import obj_table
import zipfile
import os

class dVideo():
    def __init__(self, url):
        self.yt=YouTube(url)

    def getTitle(self):
        try:
            return [True, self.yt.title]
        except Exception as e:
            print(e)
            return [False, e]
    
    def getCaptions(self):
        try:
            self.yt.streams.first()
            return [True, self.yt.captions]
        except Exception as e:
            print(e)
            return [False, e]

    def downloadCaption(self, lang):
        try:
            self.yt.streams.first()
            return [True, self.yt.captions[lang].download(self.yt.title)]
        except Exception as e:
            print(e)
            return [False, e]
    
    def getStreams(self):
        try:   
            return [True, self.yt.streams]
        except Exception as e:
            print(e)
            return [False, e] 

    def download(self, itag):
        try: 
            return [True, self.yt.streams.get_by_itag(itag).download()]
        except Exception as e:
            print(e)
            return [False, e] 

class dPlaylist():
    def __init__(self, url):
        self.p=Playlist(url)

    def numberOfVideos(self):
        try:
            return [True, len(self.p.videos)]
        except Exception as e:
            print(e)
            return [False, e]
        
    
    def getTitle(self):
        try:
            return [True, self.p.title]
        except Exception as e:
            print(e)
            return [False, e]
    
    def getQuality(self):
        try:
            quality=[]
            for i in self.p.videos:
                for j in i.streams.filter(progressive=True):
                    quality.append(j.resolution)
            return [True, quality]
        except Exception as e:
            print(e)
            return [False, e]

    def downloadVideos(self, res):
        try:
            videos = []
            for i in self.p.videos:
                itag=i.streams.filter(progressive=True, res=res)[0].itag
                video=i.streams.get_by_itag(itag)
                videos.append(video.download())
            return [True, videos]
        except Exception as e:
            print("Error: {}".format(e))
            return [False, e]

utube_views = Blueprint('utube_views', __name__)

@utube_views.route('/', methods=['POST'])
def create_url():
    try:
        url = request.form.get('url')
        obj = obj_table(url=url)
        db.session.add(obj)
        db.session.commit()
        return jsonify({"messages": "Initialized state of the object.", "id": obj.id})
    except Exception as e:
        return jsonify({"messages": str(e)}), 500
    
@utube_views.route('/video/<int:id>/getTitle/', methods=['GET'])
def getTitle(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        vid = dVideo(obj.url)
        status, res = vid.getTitle()
        if status:
            return jsonify({"messages": "Successfully fetched Title.", "title": res})
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": str(e)}), 500
    
@utube_views.route('/video/<int:id>/captionsList', methods=['GET'])
def getCaptions(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        vid = dVideo(obj.url)
        status, res = vid.getCaptions()
        #print(status, res)
        if status:
            #print(res)
            return jsonify(str(res)), 200
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500

@utube_views.route('/video/<int:id>/captionsList/download/', methods=['GET'])
def downloadCaption(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        vid = dVideo(obj.url)
        lang= request.args.get('caption_lang', default='', type=str)
        status, res =  vid.downloadCaption(lang)
        #print(status,res)
        if status:
            return send_file(str(res), as_attachment=True)
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@utube_views.route('/video/<int:id>/getStreams/', methods = ['GET'])
def getStreams(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        vid = dVideo(obj.url)
        status, res =  vid.getStreams()
        streams_info = [
            {
                'itag': stream.itag,
                'resolution': stream.resolution,
                'mime_type': stream.mime_type,
                'fps': stream.fps if stream.includes_video_track else None,
                'codecs': stream.codecs,
                'progressive': stream.is_progressive,
                'type': stream.type,
                'includes_audio_track': stream.includes_audio_track,
                'includes_video_track': stream.includes_video_track
                # Add more attributes as needed
            }
            for stream in res
        ]
        if status:
            return jsonify(streams_info), 200
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@utube_views.route('/video/<int:id>/download/<int:itag>/', methods = ['GET'])
def download_itag(id, itag):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        vid = dVideo(obj.url)
        status, res =  vid.download(itag)
        if status:
            return send_file(res, as_attachment=True)
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@utube_views.route('/playlist/<int:id>/getTitle/', methods=['GET'])
def getTitlep(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        pl = dPlaylist(obj.url)
        status, res = pl.getTitle()
        if status:
            return jsonify({"messages": "Successfully fetched Title.", "title": res})
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@utube_views.route('/playlist/<int:id>/getNVideos/', methods=['GET'])
def getVideos(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        pl = dPlaylist(obj.url)
        status, res =pl.numberOfVideos()
        if status:
            return jsonify({"number of videos": res})
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@utube_views.route('/playlist/<int:id>/getQuality/', methods=['GET'])
def getQuality(id):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"messages": "Not a valid id."}), 404
        pl = dPlaylist(obj.url)
        status, res = pl.getQuality()
        if status:
            return  jsonify(res)
        else:
            raise Exception(res)
    except Exception as e:
        return jsonify({"messages": e}), 500
    
@utube_views.route('/playlist/<int:id>/download/<string:resolution>', methods=['GET'])
def download(id, resolution):
    try:
        obj = obj_table.query.get(id)
        if not obj:
            return jsonify({"message": "Not a valid id."}), 404

        pl = dPlaylist(obj.url)

        # Validate resolution
        status, available_resolutions = pl.getQuality()
        if not status:
            raise Exception("Failed to retrieve available resolutions.")

        if resolution not in available_resolutions:
            return jsonify({"message": "Invalid Resolution"}), 400

        # Download videos
        status, download_result = pl.downloadVideos(resolution)

        zip_file_path = os.path.join(os.getcwd(), 'download.zip')
        if status:
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file_path in download_result:
                    # Get only the filename from the file_path
                    file_name = os.path.basename(file_path)
                    # Add the file to the ZIP file without any directory structure
                    zipf.write(file_path, arcname=file_name)

            return send_file(zip_file_path, as_attachment=True, download_name='files.zip')
        else:
            raise Exception(download_result)

    except Exception as e:
        return jsonify({"message": str(e)}), 500
    # finally:
    #     # Ensure to remove the temporary ZIP file after sending it
    #     if os.path.exists(zip_file_path):
    #         os.remove(zip_file_path)
    



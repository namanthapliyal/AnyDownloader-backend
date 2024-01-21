from flask import Flask, request, jsonify, render_template
from src import dinstagram as dins
from src import dInternet as dint
from src import dyoutube as dyt

app = Flask(__name__)

@app.route("/insta", methods=['GET', 'POST'])
def insta():
    try:
        flag=False
        if request.method == 'GET':
            ins=dins.dInstagram()
            flag=True
        elif request.method == 'POST':
            if not flag:
                return jsonify({"messages": "Please initialize the instagram downloader first."}), 404
            data = request.get_json()
            if data.get('method', 0):
                method = data["method"]
                if method=="login":
                    username=data["username"]
                    password=data["password"]
                    return login(username, password)
                elif method=="setUrl":
                    url=data["url"]
                    return setUrl(url)
                elif method=="getResources":
                    return getResources()
                elif method=="getMediaType":
                    return getMediaType()
                elif method == "download":
                    return download()
            else:
                return jsonify({"messages": "Invalid request."}), 405 
    except Exception as e:
        return jsonify({"messages": e}), 500
    
    def login(username, password):
        status, res=ins.login(username, password)
        if(status):
            return jsonify({'status': "good"})
        else:
            return jsonify({'messages': res}), 500
        
    def setUrl(url):
        ins.setUrl(url)
        return jsonify({'status': "good"})

    def getResources():
        status, response= ins.getResources()
        if(status):
            return jsonify({"status": "good", "response": response})
        else:
            return jsonify({"messages": response}), 500
    
    def getMediaType():
        status, response = ins.mediaType()
        if status:
            return jsonify({"status":"good", "response": response}),201
        else:
            return jsonify({"messages": response}), 500
        
    def download():
        status, response = ins.download()
        if status:
            return jsonify({"status": "good", "response": response}), 201
        else:
            return jsonify({"messages": response}), 500

# @app.route("/facebook", methods=['GET', 'POST'])
# def facebook():
#     return render_template("dFacebook.html")

@app.route("/internet", methods=['POST'])
def internet():
    try:
        data = request.get_json()
        url = data["url"]
        di = dint.dInternet(url)
        status, res = di.download()
        if(status):
            print("File successfully downloaded.")
            return jsonify({"status": "good","response":res})
        else:
            raise Exception(res)
    except Exception as e:
        print(e)
        return jsonify({"messages": e}), 500

@app.route("/utube", methods=['GET', 'POST'])
def utube():
    try:
        dtube=None
        flag=False
        if request.method == 'GET':
            flag=True
            data = request.get_json()
            url = data["url"]
            if "channel" in url:
                raise Exception("This functionality has not been implemented yet.")
            elif "list" in url:
                dtube=dyt.dPlaylist(url)
            elif "v" in url:
                dtube=dyt.dVideo(url)
            else:
                return jsonify({"messages": "Invalid URL."}), 405 
            return jsonify()
        elif request.method == "POST":
            if not flag:
                raise Exception("URL not initialized")
            data = request.get_json()
            if data.get('method', 0):
                method = data['method']
                type = data['type']
                if type == 'video':
                    if method == 'getTitle':
                        status, res = dtube.getTitle()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'getCaptions':
                        status, res = dtube.getCaptions()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'setCaptionLang':
                        lang=data['lang']
                        status, res = dtube.getCaptions(lang)
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == "downloadCaptions":
                        status, res = dtube.downloadCaptions()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'getStreams':
                        status, res = dtube.getStreams()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'setITag':
                        itag = data['itag']
                        status, res = dtube.setITag(itag)
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'download':
                        status, res = dtube.download()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    else:
                        raise Exception("No valid method selected.")
                elif type == 'playlist':
                    if method == 'getTitle':
                        status, res = dtube.getTitle()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'getQuality':
                        status, res = dtube.getQuality()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'setQuality':
                        resolution = data['resolution']
                        status, res = dtube.setQuality(resolution)
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    elif method == 'downloadVideos':
                        status, res = dtube.downloadVideos()
                        if status:
                            return jsonify({"status": "good","response":res})
                        else:
                            raise Exception(res)
                    else:
                        raise Exception("Invalid method selected.")
                else:
                    raise Exception("Select a proper type of url.")
            else:
                return jsonify({'messages': "Invalid method selected."}), 404
    except Exception as e:
        print(e)
        return jsonify({"messages": e}), 500

if __name__=="__main__":
    app.run(debug=True, port=8000)
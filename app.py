from flask import Flask, request, jsonify, render_template
from src import dinstagram as dins
from src import dInternet as dint

app = Flask(__name__)

@app.route("/insta", methods=['GET', 'POST'])
def insta():
    try:
        if request.method == 'GET':
            ins=dins.dInstagram()
        elif request.method == 'POST':
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

# @app.route("/utube", methods=['GET', 'POST'])
# def utube():
    

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

if __name__=="__main__":
    app.run(debug=True, port=8000)
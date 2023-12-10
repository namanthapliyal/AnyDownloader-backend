from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/insta")
def dInstagram():
    return render_template("dInstagram.html")

@app.route("/utube")
def dYoutube():
    return render_template("dYoutube.html")

@app.route("/facebook")
def dFacebook():
    return render_template("dFacebook.html")

@app.route("/internet")
def dInternet():
    return render_template("dInternet.html")

if __name__=="__main__":
    app.run(debug=True, port=8000)
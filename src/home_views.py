from flask import Blueprint, render_template_string

home_views = Blueprint('home_views', __name__)

@home_views.route('/')
def index():
    html_string = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Any Downloader API</title>
    </head>
    <body>
        <h1>Hello, This is an downloading service api developed by Naman Thapliyal. Please hit the endpoints for the service.</h1>
    </body>
    </html>
    """
    return render_template_string(html_string)
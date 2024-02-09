from flask import Flask
from flask_sqlalchemy  import SQLAlchemy
import os

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY']="namanthapliyal"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    #create_database(app)
    from .insta_views import insta_views
    from .internet_views import internet_views
    from .utube_views import utube_views
    from .home_views import home_views
    app.register_blueprint(insta_views, url_prefix='/insta')
    app.register_blueprint(home_views, url_prefix='/home')
    app.register_blueprint(utube_views, url_prefix='/utube')
    app.register_blueprint(internet_views, url_prefix='/internet')

    from .models import obj_table, media
    with app.app_context():
        db.create_all()
    return app



    
from . import db

class obj_table(db.Model):
    __tablename__ = 'obj_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String)
    username = db.Column(db.String, default=None)
    password = db.Column(db.String, default=None)

class media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    media_path = db.Column(db.String)
    rtype=db.Column(db.String)
    resource_id = db.Column(db.Integer, db.ForeignKey('obj_table.id'))


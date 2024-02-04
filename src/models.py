from . import db

class obj_table(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String)
    username = db.Column(db.String, default=None)
    password = db.Column(db.String, default=None)

# class media(db.Model):
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     media_url = db.Column(db.String)
#     obj_id = db.Column(db.Integer, db.ForeignKey('obj_table.id'))
#     obj_table = db.relationship('ObjTable', backref='media_entries', lazy=True)

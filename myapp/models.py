from .extensions import db 

class data(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rssi = db.Column(db.Float)
    snr = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
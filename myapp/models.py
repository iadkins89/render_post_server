from .extensions import db 

class TelemetryData(db.Model):
    timestamp = db.Column(db.timestamp, primary_key=True)
    rssi = db.Column(db.Float)
    snr = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
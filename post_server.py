from flask import Flask, render_template, request, jsonify, Response
import csv
import psycopg2
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import desc
from io import StringIO

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") # Replace with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class data(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rssi = db.Column(db.Float)
    snr = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)

def connect_to_database():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print("Unable to connect to the database")
        print(e)


@app.route('/')
def form():
    # Query existing data from the database
    latest_data = data.query.order_by(desc(data.id)).limit(10).all()
    return render_template('form.html', latest_data=latest_data)

@app.route('/download_csv', methods=['POST'])
def download_csv():
    # Query all data from the database
    all_data = data.query.all()

    # Convert data to CSV format
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(['ID', 'RSSI', 'SNR', 'Temperature', 'Humidity'])
    for d in all_data:
        csv_writer.writerow([d.id, d.rssi, d.snr, d.temperature, d.humidity])

    # Prepare CSV file for download
    csv_data.seek(0)
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=data.csv'}
    )

@app.route('/receive_data', methods=['POST'])
def receive_data():

    sensor_data = request.json
    try:
        rssi_data = sensor_data['hotspots'][0]['rssi']
        snr_data = sensor_data['hotspots'][0]['snr']
        temp_data = sensor_data['decoded']['payload'][0]['value']
        hum_data = sensor_data['decoded']['payload'][2]['value']
    except KeyError as e:
        return jsonify({'error': f'Missing key in sensor data: {str(e)}'}), 400

    try:
        save_to_database(rssi_data, snr_data, temp_data, hum_data)
        return jsonify({'message': 'Data saved to database.'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to save data to database: {str(e)}'}), 500


def save_to_database(rssi_data, snr_data, temp_data, hum_data):
    new_data = data(rssi=rssi_data, snr=snr_data, temperature=temp_data, humidity=hum_data)
    db.session.add(new_data)
    db.session.commit()


#if __name__ == '__main__':
#    app.run()

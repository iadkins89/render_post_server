from flask import Blueprint, redirect, url_for, render_template, request, jsonify, Response
import csv
from io import StringIO
from .extensions import db
from .models import data

main = Blueprint('main', __name__)

def save_to_database(rssi_data, snr_data, temp_data, hum_data):
    new_data = data(rssi=rssi_data, snr=snr_data, temperature=temp_data, humidity=hum_data)
    db.session.add(new_data)
    db.session.commit()

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
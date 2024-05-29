from flask import Blueprint, redirect, url_for, render_template, request, jsonify, Response
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
from datetime import datetime
import csv
from io import StringIO
from .extensions import db
from .models import TelemetryData
from sqlalchemy import desc

main = Blueprint('main', __name__)
dashboard = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = dashboard.server
#socketio = SocketIO(main)

main.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src='/assets/usa_blue.png', style={'height': '100px'}), width='auto'),
        dbc.Col(html.H1("South Alabama Sonde Telemetry", className="text-left", style={'color': '#154360'}), width=12)
    ], align='center'),
    dbc.Row([
        dbc.Col(dbc.Form([
            dbc.Label("CSV Filename"),
            dbc.Input(id="csv-filename", placeholder="Enter CSV filename"),
            dbc.Button("Set CSV Filename", id="set-filename-btn", color="primary", className="mt-2")
        ]), width=4),
        dbc.Col(html.Div(id='data-container', style={
            'backgroundColor': 'rgba(130,224,170,0.6)',
            'color': '#34495E',
            'height': '200px',
            'overflowY': 'scroll',
            'padding': '10px',
            'border': '2px solid #2ECC71',  # Add border here
            'borderRadius': '10px'}),
             width=8)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='temperature-graph'), width=6),
        dbc.Col(dcc.Graph(id='humidity-graph'), width=6)
    ]),
    dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)  # Update every second
])

data_store = {
    'timestamps': [],
    'rssi': [],
    'snr': [],
    'temperature': [],
    'humidity': []
}

def save_to_database(time_data, rssi_data, snr_data, temp_data, hum_data):
    new_data = TelemetryData(timestamp = time_data, rssi=rssi_data, snr=snr_data, temperature=temp_data, humidity=hum_data)
    db.session.add(new_data)
    db.session.commit()

@main.route('/set_csv_filename', methods=['POST'])
def set_csv_filename():
    global csv_filename
    data = request.json
    csv_filename = data.get('csv_filename')
    if csv_filename:
        return jsonify({'message': 'CSV filename set successfully.'}), 200
    else:
        return jsonify({'error': 'CSV filename not provided.'}), 400

@main.route('/receive_data', methods=['POST'])
def receive_data():
    global csv_filename

    sensor_data = request.json
    rssi_data = sensor_data['hotspots'][0]['rssi']
    snr_data = sensor_data['hotspots'][0]['snr']
    temp_data = sensor_data['decoded']['payload']['temperature']
    hum_data = sensor_data['decoded']['payload']['humidity']
    unix_time_data = sensor_data['decoded']['payload']['timestamp']
    timestamp = datetime.utcfromtimestamp(unix_time_data).strftime('%Y-%m-%dT%H:%M:%S')

    save_to_database(timestamp, rssi_data, snr_data, temp_data, hum_data)

    # Append to data store
    data_store['timestamps'].append(timestamp)
    data_store['rssi'].append(rssi_data)
    data_store['snr'].append(snr_data)
    data_store['temperature'].append(temp_data)
    data_store['humidity'].append(hum_data)

    if len(data_store['timestamps']) > 10:
        data_store['timestamps'].pop(0)
        data_store['rssi'].pop(0)
        data_store['snr'].pop(0)
        data_store['temperature'].pop(0)
        data_store['humidity'].pop(0)

    if csv_filename:
        save_to_csv(csv_filename, timestamp, rssi_data, snr_data, temp_data, hum_data)

    return jsonify({'message': 'Data received and broadcasted.'}), 200

def save_to_csv(csv_filename, timestamp, rssi_data, snr_data, temp_data, hum_data):
    # Save data to CSV file
    with open(csv_filename, 'a', newline='') as csvfile:
        fieldnames = ['Time', 'RSSI', 'SNR', 'Temperature', 'Humidity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()

        # Write data to CSV file
        writer.writerow({'Time': timestamp, 'RSSI': rssi_data, 'SNR': snr_data, 'Temperature': temp_data, 'Humidity': hum_data})

    return True

@dashboard.callback(
    Output('data-container', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_data_container(n):
    data_elements = [
        html.P(f"Time: {ts}, RSSI: {data_store['rssi'][i]}, SNR: {data_store['snr'][i]}, Temperature: {data_store['temperature'][i]}, Humidity: {data_store['humidity'][i]}", className='data-item')
        for i, ts in enumerate(data_store['timestamps'])
    ]
    return data_elements

@dashboard.callback(
    Output('temperature-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_temperature_graph(n):
    return {
        'data': [go.Scatter(x=data_store['timestamps'], y=data_store['temperature'], mode='lines+markers', name='Temperature', marker={'color': 'red'})],
        'layout': go.Layout(title='Temperature over Time', xaxis={'title': 'Time'}, yaxis={'title': 'Temperature (°C)'})
    }

@dashboard.callback(
    Output('humidity-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_humidity_graph(n):
    return {
        'data': [go.Scatter(x=data_store['timestamps'], y=data_store['humidity'], mode='lines+markers', name='Humidity', marker={'color': 'blue'})],
        'layout': go.Layout(title='Humidity over Time', xaxis={'title': 'Time'}, yaxis={'title': 'Humidity (%)'})
    }

@dashboard.callback(
    Output('csv-filename', 'value'),
    [Input('set-filename-btn', 'n_clicks')],
    [State('csv-filename', 'value')]
)
def set_filename(n_clicks, filename):
    if n_clicks:
        socketio.emit('set_csv_filename', {'csv_filename': filename})
        return ''
    return dashboard.no_update











"""
@main.route('/')
def form():
    # Query existing data from the database
    latest_data = data.query.order_by(desc(data.id)).limit(10).all()
    return render_template('form.html', latest_data=latest_data)

@main.route('/download_csv', methods=['POST'])
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

@main.route('/receive_data', methods=['POST'])
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
"""
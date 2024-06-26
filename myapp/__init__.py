from flask import Flask
import dash
import dash_bootstrap_components as dbc
from flask_socketio import SocketIO, emit
import os
from .extensions import db
from .routes import main

def create_app():
	app = Flask(__name__)

	app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") # Replace with your database URI
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

	dashboard = dash.Dash(__name__, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP])
	socketio = SocketIO(app)

	db.init_app(app)

	app.register_blueprint(main)

	return app
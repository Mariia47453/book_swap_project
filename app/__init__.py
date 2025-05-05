from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import and register routes
    from app import routes
    routes.register_routes(app)  # Call the function to register routes

    with app.app_context():
        db.create_all()

    return app

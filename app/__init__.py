from flask import Flask
from app.config import load_configurations, configure_logging
from .views import webhook_blueprint
import logging

def configure_flask_logging(app):
    """
    Adjust Flask's logging configuration to propagate logs to the root logger.
    """
    app.logger.propagate = True  # Enable log propagation
    app.logger.setLevel(logging.INFO)  # Set the desired logging level for Flask

def create_app():
    """
    Factory function to create and configure the Flask application.

    Returns:
        Flask app instance
    """
    # Configure logging
    try:
        configure_logging()
        logging.info("Logging configured successfully.")  # Root logger
    except Exception as e:
        print(f"Error configuring logging: {e}")
        raise

    # Initialize Flask app
    app = Flask(__name__)
    configure_flask_logging(app)  # Ensure Flask logs are propagated
    logging.info("Flask app initialized.")  # Root logger

    # Load application configurations after app creation
    try:
        load_configurations(app)
        app.logger.info("Configurations registered successfully.")
    except Exception as e:
        app.logger.error(f"Error loading configurations: {e}")
        raise

    # Register blueprints
    try:
        app.register_blueprint(webhook_blueprint)
        app.logger.info("Webhook blueprint registered successfully.")
    except Exception as e:
        app.logger.error(f"Error registering webhook blueprint: {e}")
        raise

    app.logger.info("Flask app instance created successfully.")
    return app

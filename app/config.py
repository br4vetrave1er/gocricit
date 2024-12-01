import sys
import os
from dotenv import load_dotenv
import logging
import json

def load_configurations(app):
    """
    Loads configurations from the environment and sets them in the Flask app.

    Parameters:
        app (Flask): The Flask application instance.
    """
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Set configurations from environment variables
        app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
        app.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")
        app.config["APP_ID"] = os.getenv("APP_ID")
        app.config["APP_SECRET"] = os.getenv("APP_SECRET")
        app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
        app.config["VERSION"] = os.getenv("VERSION")
        app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
        app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")
        app.config["SALES_NUMBERS"] = json.loads(os.getenv("SALES_NUMBERS"))

        # Log successful configuration loading
        logging.info("Configurations loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading configurations: {e}")
        sys.exit(1)  # Exit if configuration loading fails


def configure_logging():
    """
    Configures logging for the application.
    Logs messages to both the console and a file named 'app.log'.
    """
    try:
        # Define the logging format
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

        # Basic logging configuration
        logging.basicConfig(
            level=logging.INFO,  # Set logging level to INFO
            format=log_format,
        )

        # Add a file handler for logging to a file
        file_handler = logging.FileHandler("app.log")
        file_handler.setLevel(logging.INFO)  # Set file log level
        file_handler.setFormatter(logging.Formatter(log_format))

        # Get the root logger and add the file handler
        logger = logging.getLogger()
        logger.addHandler(file_handler)

        
    except Exception as e:
        print(f"Error configuring logging: {e}", file=sys.stderr)
        sys.exit(1)  # Exit if logging configuration fails

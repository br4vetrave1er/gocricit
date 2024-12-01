import logging
import json
import os

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, current_app

from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

# Load environment variables
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

# Initialize the blueprint for webhook
webhook_blueprint = Blueprint("webhook", __name__)


def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    Processes incoming WhatsApp messages or events such as delivery statuses.
    Handles valid messages and returns appropriate responses for unrecognized or invalid events.

    Returns:
        response: JSON response and HTTP status code.
    """
    try:
        body = request.get_json()
        # logging.info(f"Incoming request body: {json.dumps(body, indent=2)}")

        # Check if it's a WhatsApp status update
        if (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")
        ):
            logging.info("Received a WhatsApp status update.")
            return jsonify({"status": "ok"}), 200

        # Validate and process WhatsApp messages
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200

        # Respond for non-WhatsApp events
        logging.warning("Received a non-WhatsApp API event.")
        return jsonify({"status": "error", "message": "Not a WhatsApp API event"}), 404,
        

    except json.JSONDecodeError:
        logging.error("Invalid JSON provided in request body.")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500


def verify():
    """
    Handle webhook verification for WhatsApp API.

    Validates the provided mode and token and responds with the challenge token if valid.

    Returns:
        response: JSON response and HTTP status code.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            logging.info("Webhook verified successfully.")
            return challenge, 200
        else:
            logging.warning("Webhook verification failed.")
            return jsonify({"status": "error", "message": "Verification failed"}), 403

    logging.warning("Missing parameters in webhook verification request.")
    return jsonify({"status": "error", "message": "Missing parameters"}), 400


# Define GET endpoint for webhook verification
@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    """
    Handle GET requests for the webhook endpoint (verification).
    
    Returns:
        Response indicating the connection status or verification result.
    """
    return verify()


# Define POST endpoint for processing incoming webhook events
@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    """
    Handle POST requests for the webhook endpoint (incoming events).
    
    Returns:
        Response based on the event handling result.
        
    """
    return handle_message()

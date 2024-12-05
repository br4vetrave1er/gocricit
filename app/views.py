import logging
import json
import os

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, current_app
from .utils.freshchat_utils import handle_response

from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

ALLOWED_USERS = [
    "0cc7ea6e-af07-47a1-8f01-459ccc2b8812",
    "0d24626d-4911-4ff9-82b1-da7520178e72"
]


PUBLIC_KEY = """
-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkQeb/9NRzekaXAeQj59vVNPQk69BYIdylxtnhBOwyj5YhsGATyogA2DtukNG+DrCpc/hGELDVlUCZ5gXKdwI7B8UeUnsYO3cJRKh1GW+0+Sg2yp0jLgL+qCPX6OsuoTTSklFYXVGjcPM1263f0NOM7NvLz0zvGaL9pvoSyxdRfiiZSP5YveMQHj6NdxmLzC4vVs4R+zKta4r0T8YNdsZvmD2L6826B45dEpS5k6d0ouO7xa5xXLjR6hFP+uKfriDLljOThWDp7E5bc5NzEHO2uLijawhV736klQQVl7fi54a6Td4Y088AAkHvKm4p2ss2RBf2yI1XS3Jnagg3DJRdwIDAQAB
-----END RSA PUBLIC KEY-----
"""

# Load environment variables
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
# PUBLIC_KEY = os.getenv("PUBLIC_KEY")

# Initialize the blueprint for webhook
webhook_blueprint = Blueprint("webhook", __name__)


def handle_message(request):
    """
    Handle incoming webhook events from the WhatsApp API.

    Processes incoming WhatsApp messages or events such as delivery statuses.
    Handles valid messages and returns appropriate responses for unrecognized or invalid events.

    Returns:
        response: JSON response and HTTP status code.
    """
    try:
        body = request.get_json()
        if body.get("actor", {}).get("actor_type", {}) == "agent":
            return jsonify({"status": "ok", "message": "agent request made"}),200
        # if body.get("data", {}).get("message", {}).get("user_id") not in ALLOWED_USERS:
        #     return jsonify({"status": "error", "message": "User not allowed"}),403
        logging.info(f"Incoming webhook body: {json.dumps(body, indent=2)}")

        # Ignore status updates
        if body.get("action") == "status_update":
            logging.info("Ignoring status update.")
            return jsonify({"status": "ok"}), 200

        # Process only valid WhatsApp messages
        if is_valid_whatsapp_message(body):
            message_data = body.get("data", {}).get("message", {})
            # message_id = message_data.get("id")

            # # Avoid processing duplicate messages
            # if is_duplicate_message(message_id):
            #     logging.info(f"Duplicate message detected: {message_id}")
            #     return jsonify({"status": "ok"}), 200

            conversation_id = message_data.get("conversation_id")
            user_id = message_data.get("user_id")
            if not conversation_id or not user_id:
                logging.warning("Invalid message payload.")
                return jsonify({"status": "error", "message": "Invalid payload"}), 400

            # Send a message
            message_response = handle_response(body)
            logging.info(f"messages are -> {message_response}")
            if message_response[1] == 200:
                logging.info("Message sent successfully.")
                return jsonify({"status": "ok"}), 200

        logging.warning("Unrecognized or invalid event.")
        return jsonify({"status": "error", "message": "Not a valid event"}), 400

    except json.JSONDecodeError:
        logging.error("Invalid JSON in request body.")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    

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
# @signature_required
def webhook_post():
    """
    Handle POST requests for the webhook endpoint (incoming events).
    
    Returns:
        Response based on the event handling result.
        
    """

    try:
        response = handle_message(request)
        if response[1] == 200:
            return jsonify({'success': 'msg received',}), 200

    except Exception as e:
        # Handle verification failure
        return jsonify({'error': 'Verification failed', 'details': str(e)}), 400
    
    

import time
import logging
import random
import re
import json
from dotenv import load_dotenv
import requests
from flask import jsonify, current_app
from start.assistent_quickstart import sales_connect
from ..functions.agent_funtions import create_freshworks_contact, upsert_freshworks_contact
from start.agent import generate_response, generate_care_response
import os
import ast

# Global users list (consider replacing with a database for scalability)
USERS = []

load_dotenv()
DOBBEE_ID = os.getenv("DOBBEE_ASSISTANT_ID")
SALES_NUMBERS = os.getenv("SALES_NUMBERS")
escalation_numbers = json.loads(SALES_NUMBERS)
# Utility Functions
def log_http_response(response):
    """Log details of an HTTP response."""
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-Type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    """
    Create a JSON payload for sending a text message via WhatsApp API.
    
    Args:
        recipient (str): WhatsApp ID of the recipient.
        text (str): Message text content.

    Returns:
        str: JSON-formatted string for the WhatsApp API request.
    """
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    })



# Network Communication
def send_message(data):
    """ 
    Send a WhatsApp message using the Facebook Graph API.

    Args:
        data (str): JSON-formatted message payload.

    Returns:
        Response or tuple: API response or error message with HTTP status.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {current_app.config.get('ACCESS_TOKEN')}",
    }
    url = f"https://graph.facebook.com/v21.0/{current_app.config.get('PHONE_NUMBER_ID')}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=60)
        response.raise_for_status()
        log_http_response(response)
        return response
    except requests.Timeout:
        logging.error("Timeout occurred while sending the message.")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Message send failed: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500


def process_text_for_whatsapp(text):
    """
    Convert text styles to WhatsApp-compatible markdown.

    Args:
        text (str): Original text with styles.

    Returns:
        str: Text formatted for WhatsApp markdown.
    """
    text = re.sub(r"\【.*?\】", "", text).strip()  # Remove brackets
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)  # Convert **bold** to *bold*
    return text


def send_data_to_sales(cc_response):
    """
    Forward a response to sales team members via WhatsApp.

    Args:
        cc_response (str): Message content to send.
    """
    sales_numbers = current_app.config.get('SALES_NUMBERS', [])
    for number in sales_numbers:
        data_for_sales = get_text_message_input(number, cc_response)
        send_message(data_for_sales)

def new_users(wa_id):
    global USERS
    if wa_id in USERS:
        return True
    else:
        USERS.append(wa_id)
        return False

# WhatsApp Message Processing
# Temporary state for messages processed for external API responses
PROCESSED_API_RESPONSES = {}

def process_whatsapp_message(body):

    """
    Process an incoming WhatsApp message payload and handle multiple responses.

    Args:
        body (dict): Parsed JSON body of the webhook event.
    """
    try:
        # Extract sender details
        changes = body["entry"][0]["changes"][0]["value"]
        wa_id = changes["contacts"][0]["wa_id"]
        name = changes["contacts"][0]["profile"]["name"]

        # Check and upsert new users
        if new_users(wa_id):
            logging.info(f"Upserting contact for {name} ({wa_id}) in Freshworks.")
            upsert_response = upsert_freshworks_contact(name=name, mobile_number=wa_id)
            if upsert_response == 200:
                logging.info(f"Freshworks contact upserted successfully")
            else:
                logging.error(f"Error upserting contact")

        # Extract message details
        message = changes["messages"][0]
        message_id = message["id"]  # Unique ID for the message
        message_body = message["text"]["body"]

        # Log the incoming message
        logging.info(f"Received message from {name} ({wa_id}): {message_body}")
        
        # Primary Response: Generate and send primary response
        response = generate_response("support_agent", message_body, wa_id, name)
        response = process_text_for_whatsapp(response)
        data = get_text_message_input(message["from"], response)
        send_message(data)

        logging.info(f"From Here -> {ast.literal_eval(SALES_NUMBERS)}")
        # # Example Trigger: Check if message requires escalation
        # Check for escalation flag in the primary agent's response
        if "ESCALATE: true" in response:
            logging.info(f"Triggering escalation response for {name} ({wa_id}).")
            try:
                help_response = generate_care_response("sales_agent", message, wa_id)
                help_response = process_text_for_whatsapp(help_response)
                logging.info(escalation_numbers)
                for number in escalation_numbers:    
                    logging.info(f"number is -> {number}")
                    data = get_text_message_input(number, help_response)
                    logging.info(f"data is -> {data} and type -> {type(data)}")
                    send_message(data)
                logging.info(help_response)
            except Exception as e:
                logging.error(f"Response from 2 agent call: {e}")

            # help_response = process_text_for_whatsapp(help_response)

    except KeyError as e:
        logging.error(f"Missing key in payload: {e}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


# def cleanup_processed_api_responses(expiry_time=3600):
#     """
#     Remove processed message entries older than expiry_time seconds.

#     Args:
#         expiry_time (int): Time in seconds after which an entry is considered expired.
#     """
#     current_time = time.time()
#     keys_to_delete = [
#         key for key, timestamp in PROCESSED_API_RESPONSES.items()
#         if current_time - timestamp > expiry_time
#     ]
#     for key in keys_to_delete:
#         del PROCESSED_API_RESPONSES[key]
#     logging.info(f"Cleaned up {len(keys_to_delete)} old processed API responses.")




def is_valid_whatsapp_message(body):
    """
    Validate that the webhook payload contains a valid WhatsApp message.

    Args:
        body (dict): Parsed JSON body of the webhook event.

    Returns:
        bool: True if the payload is valid, False otherwise.
    """
    try:
        
        return (
            body.get("object")
            and body.get("entry")
            and body["entry"][0].get("changes")
            and body["entry"][0]["changes"][0].get("value", {}).get("messages")
        )
    except (IndexError, KeyError, TypeError):
        return False

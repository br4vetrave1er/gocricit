from dotenv import load_dotenv
import requests
import logging
from flask import jsonify
import os
from freshchat.client.configuration import FreshChatConfiguration
from freshchat.client.client import FreshChatClient

from app.start.agent import generate_response, generate_care_response
import re




load_dotenv()
FRESHCHAT_TOKEN = os.getenv("FRESHCHAT_TOKEN")
FRESHCHAT_URL = os.getenv("FRESHCHAT_URL")

def log_http_response(response):
    """Log details of an HTTP response."""
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-Type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

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


def parse_body(body):
   conversation_id = body.get("data", {}).get("message", {}).get("conversation_id")
   user_id = body.get("data", {}).get("message", {}).get("user_id")
   user_message = body.get("data", {}).get("message", {}).get("message_parts")[0].get("text").get("content")
  

   dobbee_response = generate_response("support_agent", user_message, user_id)
   dobbee_response = process_text_for_whatsapp(dobbee_response)
   logging.info(conversation_id)
   logging.info(user_id)
   logging.info(user_message)

   logging.info(f"Dobee Response -> {dobbee_response}")
   if dobbee_response:
      if "ESCALATE: true" in dobbee_response:
          logging.info(f"Triggering escalation response for ({user_id}).")
          handle_escalation_response(user_id)
      
      if conversation_id:
        return {"conversation_id": conversation_id,
              "user_id": user_id,
              "dobbee_response": dobbee_response}
      else:
          return {"conversation_id": conversation_id,
                  "user_id": user_id,
                  "dobbee_response": "Unable to process your request at this moment"}
      
      
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
      
   
def handle_escalation_response(user_id):
  cc_response = generate_care_response("sales_agent", user_id=user_id, user_phonenumber='9650546674')
  headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FRESHCHAT_TOKEN}",
    }
  url = f"https://gocricit-94335c118da0faa17054850.freshchat.com/v2/conversations/838b35b8-a8c3-4994-9b41-f277e8bfdc3f/messages"
  

  data = {
            "message_parts": [
              {
                "text": {
                  "content": cc_response
                }
              }
            ],
            "message_type": "normal",
            "actor_type": "agent",
            "user_id": "0cc7ea6e-af07-47a1-8f01-459ccc2b8812",
            "actor_id": "9d17a2ff-c579-48c0-9419-c1949f659f2d"
          }
  try:
    
    response = requests.post(url, json=data, headers=headers)
    logging.info(response.json())
    if response:
      logging.info(f"response is -> {response.json()}")
      
      return jsonify({"status": "success", "message": "message sent"}), 200
  except requests.Timeout:
      logging.error("Timeout occurred while sending the message.")
      return jsonify({"status": "error", "message": "Request timed out"}), 408
  except requests.RequestException as e:
      logging.error(f"Message send failed: {e}")
      return jsonify({"status": "error", "message": "Failed to send message"}), 500


def handle_response(body):
    """ 
    Send a WhatsApp message using the Facebook Graph API.

    Args:
        data (str): JSON-formatted message payload.

    Returns:
        Response or tuple: API response or error message with HTTP status.
    """
    # Parse the body
    parsed_data = parse_body(body)
    logging.info(f"Parsed data: {parsed_data}")
    
    # Use the parsed data
    conversation_id = parsed_data["conversation_id"]
    user_id = parsed_data["user_id"]
    dobbee_response = parsed_data["dobbee_response"]
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FRESHCHAT_TOKEN}",
    }
    url = f"https://gocricit-94335c118da0faa17054850.freshchat.com/v2/conversations/{conversation_id}/messages"
    logging.info(headers)
    data = {
              "message_parts": [
                {
                  "text": {
                    "content": dobbee_response
                  }
                }
              ],
              "message_type": "normal",
              "actor_type": "agent",
              "user_id": user_id,
              "actor_id": "9d17a2ff-c579-48c0-9419-c1949f659f2d"
            }
    try:
      # user_id = body.get("data", {}).get("message", {}).get("user_id")
      # if user_id == "your-agent-user-id":
      #   logging.info("Ignoring message from agent.")
      #   return jsonify({"status": "ok"}), 200
      response = requests.post(url, json=data, headers=headers)
      logging.info(response.json())
      if response:
        logging.info(f"response is -> {response.json()}")
        
        return jsonify({"status": "success", "message": "message sent"}), 200
    except requests.Timeout:
        logging.error("Timeout occurred while sending the message.")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Message send failed: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
import logging
import requests
import datetime

# Configuration
FRESHWORKS_API_URL = "https://gocricit.myfreshworks.com/crm/sales/api/contacts"
FRESHWORKS_API_TOKEN = "31bYtH7BqtUKbnCaTmRemA"

def create_freshworks_contact(name, mobile_number):
    """
    Calls the Freshworks API to create a contact with the provided user details.

    Parameters:
        name (str): The name of the user.
        mobile_number (str): The user's mobile number.

    Returns:
        dict: The response from the Freshworks API or an error message.
    """
    # Validate input
    # if not name or not isinstance(name, str):
    #     return {"error": "Invalid name"}

    # if not mobile_number or not isinstance(mobile_number, str):
    #     return {"error": "Invalid mobile number"}

    # Prepare payload for Freshworks API
    if not mobile_number.startswith("+"):
        mobile_number = f"+{mobile_number}"
        logging.info(f"mobile number is -> {mobile_number}")

    payload = {
        "contact": {
            "first_name": name,
            "mobile_number": mobile_number,
        }
    }
    

    headers = {
        "Authorization": f"Token token={FRESHWORKS_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        # Make the API request
        response = requests.post(
            FRESHWORKS_API_URL,
            headers=headers,
            json=payload,  # Automatically serializes to JSON
        )
        # Log response for debugging
        logging.info(f"Response: {response.status_code} -> {response.text}")
        # Check for HTTP errors
        response.raise_for_status()

        # # Return the API response as JSON
        # logging.info(f"response from freshworks -> {response.json()}")
        return response.raise_for_status()

    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}

def upsert_freshworks_contact(mobile_number, name):
    """
    Calls the Freshworks API to create or update a contact with the provided user details.
    updates last_seen field if contact is already present in CMS
    Parameters:
        name (str): The name of the user.
        mobile_number (str): The user's mobile number for unique identification.

    Returns:
        dict: The response from the Freshworks API or an error message.
    """    
    # Prepare payload for Freshworks API
    if not mobile_number.startswith("+"):
        mobile_number = f"+{mobile_number}"
        logging.info(f"mobile number is from upsert-> {mobile_number}")
    
    payload = {
        "unique_identifier":{"mobile_number": mobile_number},
        "contact": {
            "first_name": name,
            "mobile_number": mobile_number,
            "updated_at": datetime.datetime.now().isoformat(),
        }
    }
    

    headers = {
        "Authorization": f"Token token={FRESHWORKS_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        # Make the API request
        response = requests.post(
            "https://gocricit.myfreshworks.com/crm/sales/api/contacts/upsert",
            headers=headers,
            json=payload,  # Automatically serializes to JSON
        )
        # Log response for debugging
        logging.info(f"Response: {response.status_code} -> {response.text}")
        # Check for HTTP errors
        # response.raise_for_status()

        # # Return the API response as JSON
        # logging.info(f"response from freshworks -> {response.json()}")
        return response.status_code

    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}

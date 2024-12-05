import requests
import logging

def send_campaign_request(api_key, campaign_name, destination, user_name, source, media=None, template_params=None, tags=None, attributes=None):
    """
    Sends a POST request to the AiSensy campaign API.

    Args:
        api_key (str): The API key for authentication.
        campaign_name (str): The name of the campaign.
        destination (str): The destination (e.g., phone number or user ID).
        user_name (str): The user initiating the campaign.
        source (str): The source of the campaign (e.g., WhatsApp, SMS).
        media (dict, optional): Media details with `url` and `filename`.
        template_params (list, optional): List of parameters to be used in the template.
        tags (list, optional): List of tags associated with the campaign.
        attributes (dict, optional): Custom attributes for the campaign.

    Returns:
        dict: Response from the API, parsed as JSON.
    """
    url = "https://backend.aisensy.com/campaign/t1/api/v2"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "apiKey": api_key,
        "campaignName": campaign_name,
        "destination": destination,
        "userName": user_name,
        "source": source,
        "media": media if media else {},
        "templateParams": template_params if template_params else [],
        "tags": tags if tags else [],
        "attributes": attributes if attributes else {},
    }

    try:
        if not api_key or not campaign_name or not destination:
            raise ValueError("api_key, campaign_name, and destination are required fields.")

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Campaign request successful: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error in campaign request: {e}")
        return {"status": "error", "message": str(e)}

import base64
from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import os
from dotenv import load_dotenv


load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
# Replace literal \n with actual newlines
PUBLIC_KEY = PUBLIC_KEY.replace("\\n", "\n")

def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    try:
        decoded_signature = base64.b64decode(signature)

        # load the public key
        rsa_key = RSA.import_key(PUBLIC_KEY)


        hashed_payload = SHA256.new(payload)

        PKCS1_v1_5.new(rsa_key).verify(hashed_payload, decoded_signature)
        return True
    except (ValueError, TypeError) as e:
        logging.error(f"Signature validation failed: {e}")
        return False

def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get("X-Hub-Signature-256", "").replace("sha256=", "") # Removing 'sha256='
        if not validate_signature(request.data, signature):
            logging.info("Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
        return f(*args, **kwargs)

    return decorated_function
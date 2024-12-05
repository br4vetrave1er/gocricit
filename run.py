import logging
from app import create_app


# Flask app instance using the factory pattern
app = create_app()



def main():
    """
    Main function to start the Flask server.

    The server will:
    - Run on all available IP addresses (0.0.0.0)
    - Use port 8000
    - Enable debugging (for development purposes only)
    """
    logging.info("Starting Flask app on http://0.0.0.0:80")
    app.run(debug=True, port=8000,host="0.0.0.0", ssl_context=
            ("/etc/letsencrypt/live/gocirict.koreacentral.cloudapp.azure.com/fullchain.pem",
              "/etc/letsencrypt/live/gocirict.koreacentral.cloudapp.azure.com/privkey.pem"))

if __name__ == "__main__":
    main()


# sudo journalctl -u goCricit.service -f

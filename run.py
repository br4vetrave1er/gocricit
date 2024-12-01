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
    logging.info("Starting Flask app on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)

if __name__ == "__main__":
    main()

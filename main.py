from app import create_app
import logging

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

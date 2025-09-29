import os
import logging

from app import create_app

app = create_app()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    app.run(host="0.0.0.0", port=5000)

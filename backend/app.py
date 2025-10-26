import os

from flask import Flask
from utils import setup_logging
import routes

app = Flask(__name__)
setup_logging("logs", "summarizer_app.log")

routes.init_app(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import os

from flask import Flask
from utils import setup_logging
import routes

app = Flask(__name__)
setup_logging("/Users/aravind/growth/chrome-plugin/summarizer_full_app_logs", "summarizer_app.log")

routes.init_app(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

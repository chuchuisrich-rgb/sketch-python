import os
import time
from flask import Flask, g, request
from utils import setup_logging
from metrics import increment_request_count
import routes

app = Flask(__name__)
setup_logging("logs", "summarizer_app.log")

# -------------------------
# Global hooks for metrics
# -------------------------
@app.before_request
def before_request():
    g.start_time = time.time()  # record start time

@app.after_request
def after_request(response):
    latency = time.time() - g.start_time
    count_today = increment_request_count()  # update counter
    app.logger.info(
        f"{request.method} {request.path} -> {response.status_code} [{latency:.2f}s] (count={count_today})"
    )
    return response


routes.init_app(app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

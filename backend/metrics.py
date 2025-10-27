import os, json
from datetime import date

REQUEST_COUNT_FILE = "logs/request_count.json"

def increment_request_count():
    """Increment daily request counter stored in JSON file."""
    today = str(date.today())
    counts = {}
    os.makedirs(os.path.dirname(REQUEST_COUNT_FILE), exist_ok=True)

    if os.path.exists(REQUEST_COUNT_FILE):
        try:
            with open(REQUEST_COUNT_FILE, "r") as f:
                counts = json.load(f)
        except (json.JSONDecodeError, OSError):
            counts = {}

    counts[today] = counts.get(today, 0) + 1

    with open(REQUEST_COUNT_FILE, "w") as f:
        json.dump(counts, f, indent=2)

    return counts[today]


def get_request_stats():
    """Read full stats JSON file and return contents."""
    if os.path.exists(REQUEST_COUNT_FILE):
        try:
            with open(REQUEST_COUNT_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return None

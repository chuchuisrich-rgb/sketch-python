import os, json
from datetime import date

REQUEST_COUNT_FILE = "logs/request_count.json"

def increment_request_count():
    """Increment daily request counter stored in JSON file (preserves all previous days)."""
    today = str(date.today())
    counts = {}

    os.makedirs(os.path.dirname(REQUEST_COUNT_FILE), exist_ok=True)

    # Load existing counts safely
    if os.path.exists(REQUEST_COUNT_FILE):
        try:
            with open(REQUEST_COUNT_FILE, "r") as f:
                counts = json.load(f)
                if not isinstance(counts, dict):
                    counts = {}
        except (json.JSONDecodeError, OSError):
            # Log or print error if you want
            counts = {}

    # Increment today's count (merge without deleting other days)
    counts[today] = counts.get(today, 0) + 1

    # Save back merged counts
    tmp_file = REQUEST_COUNT_FILE + ".tmp"
    with open(tmp_file, "w") as f:
        json.dump(counts, f, indent=2)
    os.replace(tmp_file, REQUEST_COUNT_FILE)

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

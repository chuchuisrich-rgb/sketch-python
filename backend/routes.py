
from flask import request, jsonify
from services import summarize_text, detect_content_type, summarize_text_openai
from metrics import get_request_stats
import logging

# Below imports are for the /api/signup endpoint
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def init_app(app):

    @app.route("/api/summarize", methods=["POST"])
    def summarize():
        logger.info("📌 /summarize endpoint called")

        try:
            data = request.get_json() or {}
            text = data.get("text", "").strip()
            url = data.get("url", "").strip()

            if not text:
                logger.warning("⚠️ Empty text received")
                return jsonify({"error": "No text provided"}), 400

            logger.info(f"Received text for summarization: {text}")
            logger.info(f"📥 Received text length: {len(text)}")

            content_type = detect_content_type(request.headers.get("Referer", ""))
            logger.info(f"🧠 Detected Content Type: {content_type}")

            # summary = summarize_text(text, content_type)
            summary_openai = summarize_text_openai(text, url)
            logger.info(f"📝 Summary_openai: {summary_openai}")

            response = {
                "summary": summary_openai,
                "content_type": content_type
            }

            logger.info("✅ Summary generated successfully")
            return jsonify(response)

        except Exception as e:
            logger.exception("🔥 Summarization failed")
            return jsonify({"error": str(e)}), 500


    # -------------------------
    # Add new /api/stats endpoint
    # -------------------------
    @app.route("/api/stats", methods=["GET"])
    def stats():
        """Return daily request statistics from JSON file."""
        stats = get_request_stats()
        if not stats:
            return jsonify({"message": "No stats yet."}), 200
        return jsonify(stats), 200
    

    # -------------------------
    # Add new /api/signup endpoint
    # -------------------------
    @app.route("/api/signup", methods=["POST"])
    def signup():
        """
        Adds the submitted email to a Google Sheet.
        """
        try:
            data = request.get_json() or {}
            email = data.get("email")

            if not email or "@" not in email:
                return jsonify({"error": "Invalid email"}), 400

            # Google Sheets setup
            SHEET_NAME = "LR-Waitlist"
            SPREADSHEET_ID = "1OTMl5g7SlVXr1TYfo6MFumVNz1sRvgyn4XGRluHX-Gk"
            WORKSHEET_NAME = "Sheet1"
            CREDENTIALS_FILE = "credentials.json"  # make sure this file exists in your root folder

            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

            # Append row
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            sheet.append_row([email, timestamp])

            logger.info(f"✅ Added {email} to Google Sheet at {timestamp}")
            return jsonify({"success": True}), 200

        except Exception as e:
            logger.exception("❌ Error adding email to sheet")
            return jsonify({"error": str(e)}), 500


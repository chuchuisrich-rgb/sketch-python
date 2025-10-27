
from flask import request, jsonify
from services import summarize_text, detect_content_type, summarize_text_openai
from metrics import get_request_stats
import logging

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

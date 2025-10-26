
from flask import request, jsonify
from services import summarize_text, detect_content_type
import logging

logger = logging.getLogger(__name__)

def init_app(app):

    @app.route("/api/summarize", methods=["POST"])
    def summarize():
        logger.info("📌 /summarize endpoint called")

        try:
            data = request.get_json() or {}
            text = data.get("text", "").strip()

            if not text:
                logger.warning("⚠️ Empty text received")
                return jsonify({"error": "No text provided"}), 400

            logger.info(f"Received text for summarization: {text}")
            logger.info(f"📥 Received text length: {len(text)}")

            content_type = detect_content_type(request.headers.get("Referer", ""))
            logger.info(f"🧠 Detected Content Type: {content_type}")

            summary = summarize_text(text)

            response = {
                "summary": summary,
                "content_type": content_type
            }

            logger.info("✅ Summary generated successfully")
            return jsonify(response)

        except Exception as e:
            logger.exception("🔥 Summarization failed")
            return jsonify({"error": str(e)}), 500

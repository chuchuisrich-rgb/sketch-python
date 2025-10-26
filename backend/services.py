import logging
import os
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MAX_WORDS = 700

#load local environment variables if not in render.com
if os.getenv("RENDER") is None:
    load_dotenv()

HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_API_KEY = os.getenv("HF_API_KEY")
ONE_MINUTE_READ_5_BULLET_POINTS = "SUMMARIZE THE BELOW TEXT IN 5 SENTENCES:\n\n"

def summarize_text(text: str) -> str:
    logger.info("🧠 Using Hugging Face model for summarization")

    if len(text.split()) > MAX_WORDS:
        logger.warning("Trimming long input before sending to Hugging Face")
        text = " ".join(text.split()[:MAX_WORDS])

    text = ONE_MINUTE_READ_5_BULLET_POINTS + text
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text, "parameters": {"max_length": 350, "min_length": 40}}

    logger.info(f"🚀 Sending request to Hugging Face API: {headers}")
    logger.info(f"📄 Payload: {payload}")
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and "summary_text" in data[0]:
            summary = data[0]["summary_text"]
        else:
            summary = str(data)
        logger.info(f"✅ Summary received: {summary}...")
        return summary
    except Exception as e:
        logger.exception("🔥 Hugging Face summarization failed")
        return f"Summarization error: {e}"

def detect_content_type(url: str) -> str:
    logger.info(f"🔍 Detecting content from URL: {url}")
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if url.endswith(".pdf"):
        return "pdf"
    if "mail.google.com" in url:
        return "email"
    if "reddit.com" in url:
        return "reddit"
    if "linkedin.com" in url:
        return "linkedin"
    return "article"

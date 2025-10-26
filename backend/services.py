
import logging

logger = logging.getLogger(__name__)

MAX_WORDS = 700

def summarize_text(text: str) -> str:
    logger.info("🌀 Summarization started")
    words = text.split()

    if len(words) > MAX_WORDS:
        logger.warning(f"⚠️ Text too long: {len(words)} words. Trimming to {MAX_WORDS}")
        text = " ".join(words[:MAX_WORDS])

    sentences = text.split(".")
    summary = ". ".join(sentences[:3]).strip()

    logger.info(f"📤 Summary ready: {summary[:200]}...")
    return summary or "No meaningful summary found."

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

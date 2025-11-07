import json
import logging
import io
import os
import re
import requests
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from readability import Document
from urllib.parse import urlparse
from PyPDF2 import PdfReader
from openai import OpenAI
from googleapiclient.discovery import build

# from transformers import pipeline

logger = logging.getLogger(__name__)

MAX_WORDS = 700

#load local environment variables if not in render.com
if os.getenv("RENDER") is None:
    load_dotenv()

# Deprecated Hugging Face API details
# HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

# not working HF_API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
# not working HF_API_URL = "https://api-inference.huggingface.co/models/google/pegasus-xsum"
HF_API_URL = "https://api-inference.huggingface.co/models/Falconsai/text_summarization"


HF_API_KEY = os.getenv("HF_API_KEY")
ONE_MINUTE_READ_5_BULLET_POINTS = "SUMMARIZE THE BELOW TEXT IN 5 SENTENCES:\n\n"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)  # Uses OPENAI_API_KEY from environment

# Deprecated function using Hugging Face API for summarization
def summarize_text(text: str, content_type: str) -> str:
    logger.info("🧠 Using Hugging Face model for summarization")

    if len(text.split()) > MAX_WORDS:
        logger.warning("Trimming long input before sending to Hugging Face")
        text = " ".join(text.split()[:MAX_WORDS])

    text = ONE_MINUTE_READ_5_BULLET_POINTS + text
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text, "parameters": {"max_length": 350, "min_length": 40}}

    logger.info(f"🚀 Sending request to Hugging Face API: {headers}")
    logger.info(f"📄 Payload: {payload}")
    openai_output = summarize_text_openai(text, content_type)
    logger.info(f"✅ OpenAI summary: {openai_output}")
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

# --- Helper: Clean HTML and extract readable text ---
def extract_clean_text(url_text):
    logging.debug(f"extract_clean_text() called for URL: {url_text}")
    try:
        # resp = requests.get(url, timeout=15)
        # resp.raise_for_status()
        # html = resp.text
        doc = Document(url_text)
        title = doc.title()
        soup = BeautifulSoup(doc.summary(), "html.parser")
        text = " ".join(soup.stripped_strings)
        # logging.info(f"Extracted clean text from {url} (length={len(text)} chars)")
        return title, text
    except Exception as e:
        # logging.error(f"Error extracting clean text from {url_text}: {e}")
        logging.error(f"Error extracting clean text : {e}")
        raise

# --- Helper: Reddit ---
def extract_reddit_text(url):
    logging.debug(f"extract_reddit_text() called for URL: {url}")
    try:
        if not url.endswith(".json"):
            url = url.rstrip("/") + ".json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()[0]["data"]["children"][0]["data"]
        title = data["title"]
        body = data.get("selftext", "")
        logging.info(f"Extracted Reddit post title='{title[:60]}...' length={len(body)} chars")
        return title, body
    except Exception as e:
        logging.error(f"Error extracting Reddit post from {url}: {e}")
        raise

# --- Helper: PDF extraction ---
def extract_pdf_text(url):
    logging.debug(f"extract_pdf_text() called for URL: {url}")
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        pdf_bytes = io.BytesIO(resp.content)
        reader = PdfReader(pdf_bytes)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text += page_text + "\n"
            logging.debug(f"Extracted page {i + 1} length={len(page_text)} chars")
        title = url.split("/")[-1]
        logging.info(f"Extracted text from PDF '{title}' (total length={len(text)} chars)")
        return title, text.strip()
    except Exception as e:
        logging.error(f"Error extracting PDF text from {url}: {e}")
        raise

# --- Helper: YouTube transcript retrieval (legal) ---
def extract_youtube_transcript(url, api_key):
    logging.debug(f"extract_youtube_transcript() called for URL: {url}")
    try:
        match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        if not match:
            raise ValueError("Invalid YouTube URL")
        video_id = match.group(1)

        youtube = build("youtube", "v3", developerKey=api_key)
        logging.debug("YouTube API client initialized.")

        # Get video info
        video_response = youtube.videos().list(part="snippet", id=video_id).execute()
        title = video_response["items"][0]["snippet"]["title"]
        logging.info(f"Fetching transcript for YouTube video: {title}")

        caption_response = youtube.captions().list(part="snippet", videoId=video_id).execute()
        if not caption_response["items"]:
            logging.warning(f"No captions found for {video_id}")
            return title, None

        caption_id = caption_response["items"][0]["id"]
        caption_download_url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?tfmt=srv1&key={api_key}"

        caption_data = requests.get(caption_download_url)
        if caption_data.status_code != 200:
            logging.warning(f"Caption download failed with status {caption_data.status_code}")
            return title, None

        text = caption_data.text
        logging.info(f"Downloaded YouTube transcript length={len(text)} chars")
        return title, text
    except Exception as e:
        logging.error(f"Error extracting YouTube transcript from {url}: {e}")
        raise

def summarize_text_openai(input_text, input_url, mode="1min"):
    """
    Detects content type (URL, PDF, Reddit, YouTube, etc.),
    extracts content, and summarizes with GPT-4-Turbo.
    """
    logging.info(f"[START] summarize_text() mode={mode}")
    logger.info(f"🔑 Initializing OpenAI client with this KEY: {OPENAI_API_KEY}")
    start_time = time.time()

    # lists all the current a
    # for m in client.models.list().data:
    #     print(m.id)

    try:
        # Detect URL or plain text
        if re.match(r'https?://', input_url):
            url = input_url.strip()
            domain = urlparse(url).netloc.lower()
            logging.debug(f"Detected URL input: {url} (domain={domain})")

            if url.lower().endswith(".pdf"):
                logging.debug("Identified as PDF file.")
                title, text = extract_pdf_text(url)
                source_type = "PDF document"
            elif "reddit.com" in domain:
                logging.debug("Identified as Reddit post.")
                title, text = extract_clean_text(url)
                source_type = "Reddit post"
            elif "linkedin.com" in domain:
                logging.debug("Identified as LinkedIn content.")
                title, text = extract_clean_text(url)
                source_type = "LinkedIn post"
            elif "youtube.com" in domain or "youtu.be" in domain:
                logging.debug("Identified as YouTube video.")
                if not youtube_api_key:
                    logging.warning("YouTube API key not provided.")
                    return "⚠️ YouTube API key required to process this link legally."
                title, text = extract_youtube_transcript(url, youtube_api_key)
                if not text:
                    logging.warning("YouTube transcript not found.")
                    return f"🎥 '{title}' has no public transcript available."
                source_type = "YouTube video"
            else:
                logging.debug("Detected generic blog/news article.")
                title, text = extract_clean_text(input_text)
                source_type = "Blog or news article"

            content = f"Title: {title}\n\n{input_text}"
            logging.info(f"Source identified as {source_type}, extracted {len(input_text)} characters.")
        else:
            logging.debug("Plain text input detected.")
            source_type = "Plain text input"
            content = input_text
            logging.info(f"Received text input length={len(content)} characters.")

        # Build prompt
        # if mode == "bullets":
        #     instruction = f"Summarize this {source_type} in exactly 5 bullet points highlighting key insights."
        # else:
        #     instruction = f"Write a concise '1-minute read' summary (about 75–100 words) of this {source_type}."

        # if "reddit.com" in input_url.lower():
        #     site_instruction = "This content is from Reddit. Focus sentiment analysis on user comments and overall discussion tone."
        # elif "amazon." in input_url.lower():
        #     site_instruction = "This content is from Amazon. Focus sentiment analysis on customer reviews and overall product perception."
        # else:
        #     site_instruction = "This is general content. Focus mainly on summarization."
        # logging.info(f"Site-specific instruction: {site_instruction}")

        # instruction += " " + site_instruction

        # Limit content length for token safety
        content_snippet = content[:30000]
        logging.debug(f"Prompt prepared (length={len(content_snippet)} chars).")

        # Build final message
        # prompt = f"{instruction}\n\n{content_snippet}"

        prompt = f"""
            You are an analytical AI that summarizes and, if applicable, performs sentiment analysis.

            If the content is from Reddit or Amazon, include sentiment analysis based on comments or reviews.
            If it is a general blog or news article, summarize only.

            Respond **strictly in JSON** with these possible fields:
            {{
            "summary": "3–5 sentence summary of the content",
            "sentiment": "Positive / Neutral / Negative (only for Reddit or Amazon)",
            "positive_percent": <number, optional>,
            "neutral_percent": <number, optional>,
            "negative_percent": <number, optional>
            }}

            Content:
            {content_snippet}
            """
        
        logging.debug(f"Final prompt starts with: {prompt[:200]}...")

        # Make GPT-4-Turbo call
        logging.info("Calling gpt-4o-mini for summarization...")
        gpt_start = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        #Try to use local
        # response = summarize_text_local(prompt)
        logging.info("##" * 20)
        logging.info(f"Full Hugging Face response: {response}")
        logging.info("##" * 20)
 
        gpt_end = time.time()

        raw_output = response.choices[0].message.content.strip()
        logging.info(f"Raw GPT output received in {gpt_end - gpt_start:.2f}s, length={len(raw_output)} chars.")
        logging.debug(f"Raw output preview: {raw_output[:300]}...")

        logging.info("##" * 20)
        logging.info(f"Full GPT output: {raw_output}")
        logging.info("##" * 20)
        hf_result = call_hugging_face(prompt)
        logging.info(f"Full Hugging Face output: {hf_result}")
        logging.info("##" * 20)


        # Try to parse JSON (GPT sometimes returns extra formatting)
        try:
            result = json.loads(raw_output)
            summary_text = result.get("summary", "")
            sentiment = result.get("sentiment")
            pos = result.get("positive_percent")
            neu = result.get("neutral_percent")
            neg = result.get("negative_percent")

            logging.info(f"✅ Parsed JSON successfully. Sentiment={sentiment}, +%={pos}, n%={neu}, -%={neg}")

        except json.JSONDecodeError:
            logging.warning("⚠️ Failed to parse GPT response as JSON. Returning raw summary text.")
            result = {"summary": raw_output, "sentiment": None}
            summary_text = raw_output

        logging.info(f"[END] summarize_text() total time={time.time() - start_time:.2f}s")
        return result


    except Exception as e:
        logging.exception(f"❌ Exception in summarize_text(): {e}")
        return f"Error with the summarization service. Please try again later."
    

# def summarize_text_local(text: str) -> str:
#     """
#     Summarize text locally using a lightweight model.
#     Requires 'transformers' and 'torch' installed.
#     """
#     summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
#     summary = summarizer(text, max_length=200, min_length=40, do_sample=False)[0]['summary_text']
#     return summary

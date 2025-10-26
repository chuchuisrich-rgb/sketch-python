
# Simple Summarizer App

Backend + Chrome Extension (Option 1 UI)

## Backend Setup

```
cd backend
pip install -r requirements.txt
python app.py
```

To deploy on Render, push this folder and Render will auto-detect Flask.

---

## API
POST /api/summarize  
Body: `{ "text": "Your text to summarize" }`

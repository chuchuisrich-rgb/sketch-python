
const API_URL = "http://127.0.0.1:5000/api/summarize";

document.getElementById("summarizeBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [{ result: pageText }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText
  });

  document.getElementById("disclaimer").innerText = "Summarizing...";
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: tab.url, text: pageText })
    });
    const data = await response.json();
    const summaryDiv = document.getElementById("summaryCard");
    summaryDiv.classList.remove("hidden");
    document.getElementById("summaryText").innerText = data.summary || "Error summarizing.";
    document.getElementById("disclaimer").innerText = data.content_type ? "Detected: " + data.content_type : "";
  } catch (err) {
    document.getElementById("disclaimer").innerText = "Error: " + err.message;
  }
});

document.getElementById("copyBtn").addEventListener("click", () => {
  const text = document.getElementById("summaryText").innerText;
  navigator.clipboard.writeText(text);
  document.getElementById("copyBtn").innerText = "✅ Copied!";
  setTimeout(() => document.getElementById("copyBtn").innerText = "📋 Copy", 1500);
});

document.getElementById("listenBtn").addEventListener("click", () => {
  const summaryText = document.getElementById("summaryText").innerText;

  if (!summaryText || summaryText.trim().length === 0) {
    document.getElementById("disclaimer").innerText = "No summary available to read.";
    return;
  }

  // Cancel any ongoing speech first
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(summaryText);
  utterance.lang = "en-US"; // you can change voice/language
  utterance.rate = 1.0;     // normal speed
  utterance.pitch = 1.0;

  // Optional: pick a specific voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.name.toLowerCase().includes("female") || v.name.toLowerCase().includes("google"));
  if (preferred) utterance.voice = preferred;

  // Update button text while speaking
  const listenBtn = document.getElementById("listenBtn");
  listenBtn.innerText = "🔈 Playing...";
  utterance.onend = () => { listenBtn.innerText = "🔊 Listen"; };

  window.speechSynthesis.speak(utterance);
});

document.getElementById("stopBtn").addEventListener("click", () => {
  window.speechSynthesis.cancel();
});

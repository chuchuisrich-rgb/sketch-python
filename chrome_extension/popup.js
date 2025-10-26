
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
      body: JSON.stringify({ text: pageText })
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

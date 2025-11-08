
// Local backend url
// const API_URL = "http://127.0.0.1:5000/api/summarize"; 
// Production backend url
// const API_URL = "https://sketch-python.onrender.com/api/summarize";

// Detect environment
const isLocal = !chrome.runtime.getManifest().update_url; // only true in dev unpacked mode
const BASE_URL = isLocal 
  ? "http://127.0.0.1:5000" 
  : "https://sketch-python.onrender.com";

document.getElementById("summarizeBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [{ result: pageText }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText
  });

  document.getElementById("disclaimer").innerText = "Summarizing...";
  document.getElementById("buttonGroup").classList.add("hidden");

  try {
    // ✅ Always use the same backend endpoint
    const endpoint = "/api/summarize";
    const API_URL = `${BASE_URL}${endpoint}`;

    console.log("📡 Using unified API URL:", API_URL);

    // Add the URL so backend can detect Reddit/Amazon
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: tab.url, text: pageText })
    });

    console.log("✅ Response status:", response.status, response.statusText);

    // Handle credit or server errors gracefully
    if (!response.ok || true) {
      console.warn("⚠️ Backend error:", response.status);

      // Hide existing elements
      document.getElementById("buttonGroup").classList.add("hidden");
      document.getElementById("summaryCard").classList.add("hidden");

      // Load the external error template HTML
      const summaryDiv = document.getElementById("summaryCard");
      summaryDiv.classList.remove("hidden");

      try {
        const resp = await fetch(chrome.runtime.getURL("error_template.html"));
        const html = await resp.text();
        summaryDiv.innerHTML = html;
      } catch (err) {
        console.error("❌ Failed to load error_template.html:", err);
        summaryDiv.innerHTML = "<p>Error loading template.</p>";
      }

      // Attach listener for Notify button (after HTML injected)
      const notifyBtn = summaryDiv.querySelector("#notify-btn");
      notifyBtn.addEventListener("click", async () => {
        const email = summaryDiv.querySelector("#email-input").value.trim();
        const thanks = summaryDiv.querySelector("#thanks");

        if (!email || !email.includes("@")) {
          alert("Please enter a valid email address.");
          return;
        }

        try {
          const res = await fetch(`${BASE_URL}/api/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
          });
          if (res.ok) thanks.style.display = "block";
          else alert("Something went wrong. Please try again later.");
        } catch (err) {
          alert("Network error. Please try again later.");
        }
      });

      // Stop further code execution
      return;
    }

    const api_response = await response.json();
    const complete_data = api_response.summary;
    console.log("🧾 Full API response:", JSON.stringify(complete_data, null, 2));

    let data;
    try {
      // Remove markdown-style formatting (```json ... ```)
      const cleanJSON = complete_data.summary.replace(/```json|```/g, "").trim();

      // Parse to object
      data = JSON.parse(cleanJSON);
      console.log("✅ Parsed summary JSON:", data);
    } catch (error) {
      console.error("❌ Error parsing summary JSON:", error);
    }

    // Show the summary card
    const summaryDiv = document.getElementById("summaryCard");
    summaryDiv.classList.remove("hidden");

    // ✅ Show buttons only now
    document.getElementById("buttonGroup").classList.remove("hidden");

    // 🧩 Always show summary
    const summaryTextElem = document.getElementById("summaryText");
    summaryTextElem.innerText = data.summary || "Error summarizing.";
    console.log("📝 Summary text:", data.summary);

    // 🎨 Handle sentiment color-coded block
    const sentimentBlock = document.getElementById("sentimentBlock");
    const badge = document.getElementById("sentimentBadge");
    const breakdown = document.getElementById("sentimentBreakdown");

    // Hide sentiment block by default
    sentimentBlock.classList.add("hidden");

    // Only show if backend included sentiment fields
    if (data.sentiment) {
      sentimentBlock.classList.remove("hidden");

      // Set badge text
      let sentimentEmoji = "😐"; // default neutral
      if (data.sentiment.toLowerCase().includes("pos")) sentimentEmoji = "😊";
      else if (data.sentiment.toLowerCase().includes("neg")) sentimentEmoji = "😞";

      badge.innerText = `${sentimentEmoji} ${data.sentiment}`;

      badge.className = "sentiment"; // reset previous classes

      // Add color class
      if (data.sentiment.toLowerCase().includes("pos")) badge.classList.add("positive");
      else if (data.sentiment.toLowerCase().includes("neu")) badge.classList.add("neutral");
      else if (data.sentiment.toLowerCase().includes("neg")) badge.classList.add("negative");

      // Show breakdown if available
      if (
        data.positive_percent !== undefined &&
        data.neutral_percent !== undefined &&
        data.negative_percent !== undefined
      ) {
        breakdown.innerText =
          `${data.positive_percent}% positive, ` +
          `${data.neutral_percent}% neutral, ` +
          `${data.negative_percent}% negative`;
      } else {
        breakdown.innerText = "";
      }
    }

    console.log("tab url value:", tab.url);
    // Update disclaimer based on detected content type
    if (tab.url.includes("reddit.com")) {
      document.getElementById("disclaimer").innerText = "Detected: Reddit discussion";
    } else if (tab.url.includes("amazon.")) {
      document.getElementById("disclaimer").innerText = "Detected: Amazon product page";
    } else {
      document.getElementById("disclaimer").innerText = "Detected: General webpage";
    }

  } catch (err) {
    console.error("❌ Error fetching summary:", err);
    document.getElementById("disclaimer").innerText = "Error: " + err.message;
    document.getElementById("buttonGroup").classList.add("hidden");
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

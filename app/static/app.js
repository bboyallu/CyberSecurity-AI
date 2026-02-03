const scanForm = document.getElementById("scan-form");
const scanOutput = document.getElementById("scan-output");
const alertButton = document.getElementById("alert-btn");
const alertsContainer = document.getElementById("alerts");
const chatForm = document.getElementById("chat-form");
const chatLog = document.getElementById("chat-log");
const speakButton = document.getElementById("speak-btn");

let lastReply = "";

const renderAlert = (alert) => `
  <div class="alert ${alert.severity}">
    <strong>${alert.id}</strong>
    <span>${alert.summary}</span>
    <em>${new Date(alert.timestamp).toLocaleString()}</em>
  </div>
`;

const renderScan = (scan) => `
  <h3>${scan.target}</h3>
  <p><strong>Depth:</strong> ${scan.depth}</p>
  <p><strong>Risk Score:</strong> ${scan.risk_score}</p>
  <ul>
    ${scan.findings.map((finding) => `<li>${finding}</li>`).join("")}
  </ul>
  <small>${new Date(scan.timestamp).toLocaleString()}</small>
`;

const addChatMessage = (role, text) => {
  const entry = document.createElement("div");
  entry.className = `chat-message ${role}`;
  entry.innerHTML = `<span>${role === "user" ? "You" : "CyberShield AI"}</span><p>${text}</p>`;
  chatLog.appendChild(entry);
  chatLog.scrollTop = chatLog.scrollHeight;
};

const fetchAlerts = async () => {
  const response = await fetch("/api/alerts");
  const data = await response.json();
  alertsContainer.innerHTML = data.alerts.map(renderAlert).join("");
};

scanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(scanForm);
  const payload = {
    target: formData.get("target"),
    depth: formData.get("depth"),
  };
  const response = await fetch("/api/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  scanOutput.innerHTML = renderScan(data);
  fetchAlerts();
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(chatForm);
  const message = formData.get("message");
  addChatMessage("user", message);
  chatForm.reset();
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await response.json();
  lastReply = data.response;
  addChatMessage("assistant", data.response);
});

speakButton.addEventListener("click", () => {
  if (!lastReply) {
    return;
  }
  const utterance = new SpeechSynthesisUtterance(lastReply);
  utterance.rate = 1;
  utterance.pitch = 1.1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
});

alertButton.addEventListener("click", fetchAlerts);

fetchAlerts();

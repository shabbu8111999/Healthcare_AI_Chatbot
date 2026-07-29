let threadId = localStorage.getItem("healthcare_chatbot_thread_id");
let chats = [];
let openMenuThreadId = null;
let attachedFile = null; // { filename, text }

const chatDiv = document.getElementById("chat");
const reviewArea = document.getElementById("review-area");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const chatListEl = document.getElementById("chat-list");
const newChatButton = document.getElementById("new-chat-button");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");
const sidebarCollapseButton = document.getElementById("sidebar-collapse-button");
const attachButton = document.getElementById("attach-button");
const fileInput = document.getElementById("file-input");
const attachmentChipArea = document.getElementById("attachment-chip-area");
const micButton = document.getElementById("mic-button");
const downloadArea = document.getElementById("download-area");

const PULSE_SVG =
  '<svg class="pulse" viewBox="0 0 100 40" preserveAspectRatio="none">' +
  '<path class="pulse-path" d="M0,20 L20,20 L25,5 L30,35 L35,20 L50,20 L55,10 L60,20 L100,20" /></svg>';

const PENCIL_ICON =
  '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
  '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>';

const TRASH_ICON =
  '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
  '<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>' +
  '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>';

const MIC_ICON =
  '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
  '<path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>' +
  '<path d="M19 10v1a7 7 0 0 1-14 0v-1"/><line x1="12" y1="18" x2="12" y2="22"/></svg>';

const PDF_ICON =
  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
  '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/></svg>';

micButton.innerHTML = MIC_ICON;

function scrollToBottom() {
  chatDiv.scrollTop = chatDiv.scrollHeight;
}

/* chat messages */

function renderMessage(role, content) {
  const div = document.createElement("div");
  div.className = "msg " + (role === "user" ? "user" : "assistant");

  if (role === "user") {
    div.textContent = content;
  } else {
    // assistant replies may contain markdown, this renders it properly
    // instead of showing raw ** and - marks
    div.innerHTML = marked.parse(content);
  }

  chatDiv.appendChild(div);
  return div;
}

function showTyping() {
  const bubble = document.createElement("div");
  bubble.className = "msg assistant typing";
  bubble.id = "typing-indicator";
  bubble.innerHTML = PULSE_SVG + "<span>Thinking</span>";
  chatDiv.appendChild(bubble);
  scrollToBottom();
}

function renderSources(sources) {
  if (!sources || sources.length === 0) return "";
  return sources.map(function (s) {
    return s.topic + " (" + s.source + ")";
  }).join(", ");
}

function renderDownloadLinks(hasRealQuestion) {
  downloadArea.innerHTML = "";
  if (!threadId || !hasRealQuestion) return;

  const pdfLink = document.createElement("a");
  pdfLink.href = "/export/" + threadId + "/pdf";
  pdfLink.innerHTML = PDF_ICON + "<span>Download PDF</span>";

  const docxLink = document.createElement("a");
  docxLink.href = "/export/" + threadId + "/docx";
  docxLink.innerHTML = PDF_ICON + "<span>Download Word</span>";

  downloadArea.appendChild(pdfLink);
  downloadArea.appendChild(docxLink);
}

function renderState(data) {
  threadId = data.thread_id;
  localStorage.setItem("healthcare_chatbot_thread_id", threadId);

  chatDiv.innerHTML = "";
  data.history.forEach(function (m) {
    renderMessage(m.role, m.content);
  });

  reviewArea.innerHTML = "";
  if (data.pending_review) {
    const box = document.createElement("div");
    box.className = "review-box";

    const label = document.createElement("span");
    label.className = "review-label";
    label.textContent = "Waiting for review";
    box.appendChild(label);

    const answerText = document.createElement("div");
    answerText.className = "review-answer";
    answerText.innerHTML = marked.parse(data.pending_review.answer);
    box.appendChild(answerText);

    const sourcesText = document.createElement("div");
    sourcesText.className = "sources";
    sourcesText.textContent = renderSources(data.pending_review.sources);
    box.appendChild(sourcesText);

    const buttonRow = document.createElement("div");
    buttonRow.className = "review-buttons";

    const approveBtn = document.createElement("button");
    approveBtn.className = "approve";
    approveBtn.textContent = "Approve answer";
    approveBtn.addEventListener("click", function () {
      sendReview("approve");
    });

    const rejectBtn = document.createElement("button");
    rejectBtn.className = "regenerate";
    rejectBtn.textContent = "Regenerate";
    rejectBtn.addEventListener("click", function () {
      sendReview("reject");
    });

    buttonRow.appendChild(approveBtn);
    buttonRow.appendChild(rejectBtn);
    box.appendChild(buttonRow);

    reviewArea.appendChild(box);
  }

  renderDownloadLinks(data.has_real_question);
  scrollToBottom();
}

async function loadHistory() {
  if (!threadId) {
    chatDiv.innerHTML = "";
    reviewArea.innerHTML = "";
    downloadArea.innerHTML = "";
    return;
  }
  const res = await fetch("/history/" + threadId);
  if (res.ok) renderState(await res.json());
}

/* sending messages and reviews */

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendButton.disabled = true;

  renderMessage("user", message);
  showTyping();
  scrollToBottom();

  const attachmentText = attachedFile ? attachedFile.text : null;
  clearAttachment();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: threadId,
        message: message,
        attachment_text: attachmentText,
      }),
    });
    renderState(await res.json());
    await loadChatList();
  } finally {
    sendButton.disabled = false;
  }
}

async function sendReview(decision) {
  if (decision === "reject") {
    showTyping();
    scrollToBottom();
  }

  const res = await fetch("/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, decision: decision }),
  });
  renderState(await res.json());
}

/* file attachment */

function renderAttachmentChip() {
  attachmentChipArea.innerHTML = "";
  if (!attachedFile) return;

  const chip = document.createElement("div");
  chip.className = "attachment-chip";

  const label = document.createElement("span");
  label.textContent = "📄 " + attachedFile.filename;

  const removeBtn = document.createElement("button");
  removeBtn.textContent = "\u2715";
  removeBtn.setAttribute("aria-label", "Remove attachment");
  removeBtn.addEventListener("click", clearAttachment);

  chip.appendChild(label);
  chip.appendChild(removeBtn);
  attachmentChipArea.appendChild(chip);
}

function clearAttachment() {
  attachedFile = null;
  fileInput.value = "";
  renderAttachmentChip();
}

attachButton.addEventListener("click", function () {
  fileInput.click();
});

fileInput.addEventListener("change", async function () {
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  attachButton.disabled = true;
  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    if (res.ok) {
      const data = await res.json();
      attachedFile = { filename: data.filename, text: data.text };
      renderAttachmentChip();
    }
  } finally {
    attachButton.disabled = false;
  }
});

/* speech to text, using the browser's built in Web Speech API, no
   external service or key needed */

const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

if (SpeechRecognitionApi) {
  recognition = new SpeechRecognitionApi();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.addEventListener("result", function (event) {
    const transcript = event.results[0][0].transcript;
    input.value = (input.value ? input.value + " " : "") + transcript;
  });

  recognition.addEventListener("end", function () {
    isListening = false;
    micButton.classList.remove("listening");
  });

  recognition.addEventListener("error", function () {
    isListening = false;
    micButton.classList.remove("listening");
  });

  micButton.addEventListener("click", function () {
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
      isListening = true;
      micButton.classList.add("listening");
    }
  });
} else {
  // browser does not support speech recognition, hide the button
  // rather than offer something that will not work
  micButton.style.display = "none";
}

/* sidebar: chat list, switching, new chat, rename, delete */

async function loadChatList() {
  const res = await fetch("/chats");
  if (!res.ok) return;
  chats = await res.json();
  renderChatList();
}

function renderChatList() {
  chatListEl.innerHTML = "";

  chats.forEach(function (chat) {
    const item = document.createElement("div");
    item.className = "chat-item" + (chat.thread_id === threadId ? " active" : "");

    const titleSpan = document.createElement("span");
    titleSpan.className = "chat-title";
    titleSpan.textContent = chat.title || "New chat";
    titleSpan.addEventListener("click", function () {
      switchChat(chat.thread_id);
    });

    const menuButton = document.createElement("button");
    menuButton.className = "chat-menu-button";
    menuButton.setAttribute("aria-label", "Chat options");
    menuButton.textContent = "\u22EE";
    menuButton.addEventListener("click", function (e) {
      e.stopPropagation();
      openChatMenu(menuButton, chat);
    });

    item.appendChild(titleSpan);
    item.appendChild(menuButton);
    chatListEl.appendChild(item);
  });
}

// one shared dropdown, appended to the very end of the page, not
// nested inside the scrolling sidebar list, so it can never get
// clipped or trigger a stray scrollbar the way a nested one did
const chatMenuDropdown = document.createElement("div");
chatMenuDropdown.className = "chat-menu-dropdown";
document.body.appendChild(chatMenuDropdown);

function openChatMenu(button, chat) {
  chatMenuDropdown.innerHTML = "";

  const renameBtn = document.createElement("button");
  renameBtn.innerHTML = PENCIL_ICON + "<span>Rename</span>";
  renameBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    closeChatMenu();
    renameChat(chat.thread_id, chat.title);
  });

  const deleteBtn = document.createElement("button");
  deleteBtn.className = "danger";
  deleteBtn.innerHTML = TRASH_ICON + "<span>Delete</span>";
  deleteBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    closeChatMenu();
    deleteChat(chat.thread_id);
  });

  chatMenuDropdown.appendChild(renameBtn);
  chatMenuDropdown.appendChild(deleteBtn);

  const rect = button.getBoundingClientRect();
  const dropdownWidth = 170;
  chatMenuDropdown.style.top = rect.bottom + 6 + "px";
  chatMenuDropdown.style.left = Math.max(8, rect.right - dropdownWidth) + "px";
  chatMenuDropdown.classList.add("open");
  openMenuThreadId = chat.thread_id;
}

function closeChatMenu() {
  chatMenuDropdown.classList.remove("open");
  openMenuThreadId = null;
}

async function switchChat(newThreadId) {
  if (newThreadId === threadId) return;
  threadId = newThreadId;
  localStorage.setItem("healthcare_chatbot_thread_id", threadId);
  await loadHistory();
  renderChatList();
}

function startNewChat() {
  threadId = null;
  localStorage.removeItem("healthcare_chatbot_thread_id");
  chatDiv.innerHTML = "";
  reviewArea.innerHTML = "";
  downloadArea.innerHTML = "";
  clearAttachment();
  renderChatList();
  input.focus();
}

async function renameChat(id, currentTitle) {
  const newTitle = prompt("Rename chat", currentTitle);
  if (!newTitle || !newTitle.trim()) return;
  await fetch("/chats/" + id + "/rename", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: newTitle.trim() }),
  });
  await loadChatList();
}

async function deleteChat(id) {
  const confirmed = confirm("Delete this chat? This cannot be undone.");
  if (!confirmed) return;

  await fetch("/chats/" + id, { method: "DELETE" });

  if (id === threadId) {
    startNewChat();
  }
  await loadChatList();
}

/* sidebar collapse, works the same on any screen size */

function collapseSidebar() {
  sidebar.classList.add("collapsed");
  sidebarToggle.classList.add("visible");
}

function expandSidebar() {
  sidebar.classList.remove("collapsed");
  sidebarToggle.classList.remove("visible");
}

sidebarCollapseButton.addEventListener("click", collapseSidebar);
sidebarToggle.addEventListener("click", expandSidebar);

/* wiring */

sendButton.addEventListener("click", sendMessage);
input.addEventListener("keydown", function (e) {
  if (e.key === "Enter") sendMessage();
});

newChatButton.addEventListener("click", startNewChat);

// closes the open chat menu when clicking anywhere else on the page
document.addEventListener("click", function (e) {
  if (openMenuThreadId !== null && !chatMenuDropdown.contains(e.target)) {
    closeChatMenu();
  }
});

loadChatList();
loadHistory();
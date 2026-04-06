// ─── STATE ────────────────────────────────────────────────────────────────
const STORAGE_KEY = 'ct_sessions';
const MAX_SESSIONS = 20;
let username = '';
let currentSessionId = null;
let sessions = {};
let isLoading = false;

// ─── DOM REFS ─────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const messagesEl    = $('messages');
const welcomeScreen = $('welcomeScreen');
const welcomeTitle  = $('welcomeTitle');
const messageInput  = $('messageInput');
const sendBtn       = $('sendBtn');
const charCount     = $('charCount');
const historyList   = $('historyList');
const profileBtn    = $('profileBtn');
const profilePanel  = $('profilePanel');
const panelOverlay  = $('panelOverlay');
const avatarDisplay = $('avatarDisplay');
const usernameDisplay = $('usernameDisplay');
const panelAvatar   = $('panelAvatar');
const panelName     = $('panelName');
const sessionLabel  = $('sessionLabel');
const resetModal    = $('resetModal');
const sidebarToggle = $('sidebarToggle');
const suggestionChips = $('suggestionChips');

// ─── INIT ─────────────────────────────────────────────────────────────────
function init() {
  username = localStorage.getItem('ct_username');
  if (!username) {
    window.location.href = '/';
    return;
  }

  // Update UI with username
  const initial = username.charAt(0).toUpperCase();
  avatarDisplay.textContent    = initial;
  panelAvatar.textContent      = initial;
  usernameDisplay.textContent  = username;
  panelName.textContent        = username;
  welcomeTitle.textContent     = `Hey, ${username.split(' ')[0]}! 👋`;

  // Load stored sessions
  sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');

  // Start a new session
  startNewSession();
  renderHistoryList();
  bindEvents();
}

// ─── SESSION MANAGEMENT ───────────────────────────────────────────────────
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function startNewSession() {
  currentSessionId = generateId();
  sessions[currentSessionId] = { title: 'New Session', messages: [], createdAt: Date.now() };
  persistSessions();
  clearChatUI();
  renderHistoryList();
  sessionLabel.textContent = 'New Session';
}

function loadSession(id) {
  if (!sessions[id]) return;
  currentSessionId = id;
  clearChatUI();

  const { messages, title } = sessions[id];
  sessionLabel.textContent = title || 'Session';

  if (messages.length === 0) {
    welcomeScreen.style.display = 'flex';
    return;
  }

  welcomeScreen.style.display = 'none';
  messages.forEach(m => renderMessage(m.role, m.content, false));
  scrollToBottom();
  renderHistoryList();
}

function deleteSession(id, e) {
  e.stopPropagation();
  delete sessions[id];
  persistSessions();

  if (id === currentSessionId) startNewSession();
  else renderHistoryList();
}

function persistSessions() {
  // Keep only the most recent MAX_SESSIONS
  const keys = Object.keys(sessions).sort((a, b) => (sessions[b].createdAt || 0) - (sessions[a].createdAt || 0));
  if (keys.length > MAX_SESSIONS) {
    keys.slice(MAX_SESSIONS).forEach(k => delete sessions[k]);
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

// ─── RENDER HISTORY SIDEBAR ───────────────────────────────────────────────
function renderHistoryList() {
  historyList.innerHTML = '';
  const keys = Object.keys(sessions).sort((a, b) => (sessions[b].createdAt || 0) - (sessions[a].createdAt || 0));

  if (keys.length === 0) {
    historyList.innerHTML = '<div class="history-empty">No sessions yet</div>';
    return;
  }

  keys.forEach(id => {
    const s = sessions[id];
    if (!s) return;
    const item = document.createElement('div');
    item.className = 'history-item' + (id === currentSessionId ? ' active' : '');
    item.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="1.5"/></svg>
      <span class="history-item-text">${escapeHtml(s.title || 'Session')}</span>
      <button class="history-item-del" title="Delete">
        <svg viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
    `;
    item.querySelector('.history-item-del').addEventListener('click', (e) => deleteSession(id, e));
    item.addEventListener('click', () => loadSession(id));
    historyList.appendChild(item);
  });
}

// ─── CHAT LOGIC ───────────────────────────────────────────────────────────
async function sendMessage(text) {
  if (isLoading || !text.trim()) return;

  const content = text.trim();
  messageInput.value = '';
  autoResize();
  updateCharCount();
  sendBtn.disabled = true;

  // Hide welcome, show messages
  welcomeScreen.style.display = 'none';
  renderMessage('user', content);

  // Update session title from first message
  const session = sessions[currentSessionId];
  if (session && session.messages.length === 0) {
    session.title = content.slice(0, 40) + (content.length > 40 ? '…' : '');
    sessionLabel.textContent = session.title;
  }

  // Store user message
  if (session) {
    session.messages.push({ role: 'user', content });
    persistSessions();
  }

  // Show typing indicator
  const typingEl = showTypingIndicator();
  isLoading = true;

  try {
    // Build history for API (last 5 pairs)
    const history = session ? session.messages.slice(0, -1).slice(-10) : [];

    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: content, history, username })
    });

    const data = await res.json();
    typingEl.remove();

    if (!res.ok || data.error) {
      renderMessage('ai', data.error || 'Something went wrong. Please try again.', true, true);
    } else {
      renderMessage('ai', data.reply);
      if (session) {
        session.messages.push({ role: 'assistant', content: data.reply });
        persistSessions();
      }
    }

  } catch (err) {
    typingEl.remove();
    renderMessage('ai', 'Network error. Please check your connection and try again.', true, true);
  } finally {
    isLoading = false;
    sendBtn.disabled = messageInput.value.trim().length === 0;
    renderHistoryList();
    scrollToBottom();
  }
}

// ─── RENDER MESSAGE ───────────────────────────────────────────────────────
function renderMessage(role, content, animate = true, isError = false) {
  const group = document.createElement('div');
  group.className = `msg-group ${role}`;
  if (!animate) group.style.animation = 'none';

  const initial = role === 'user' ? username.charAt(0).toUpperCase() : 'AI';
  const name    = role === 'user' ? username : 'ChatTutor';

  group.innerHTML = `
    <div class="msg-avatar">${initial}</div>
    <div class="msg-bubble-wrap">
      <div class="msg-name">${escapeHtml(name)}</div>
      <div class="msg-bubble ${isError ? 'msg-error' : ''}">${role === 'ai' ? formatMarkdown(content) : escapeHtml(content)}</div>
    </div>
  `;

  messagesEl.appendChild(group);
  if (animate) scrollToBottom();
  return group;
}

function showTypingIndicator() {
  const group = document.createElement('div');
  group.className = 'msg-group ai';
  group.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-bubble-wrap">
      <div class="msg-name">ChatTutor</div>
      <div class="msg-bubble">
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>
  `;
  messagesEl.appendChild(group);
  scrollToBottom();
  return group;
}

// ─── MARKDOWN FORMATTER ───────────────────────────────────────────────────
function formatMarkdown(text) {
  let html = escapeHtml(text);

  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
    `<pre><code>${code.trim()}</code></pre>`);

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Unordered list
  html = html.replace(/^[-*•] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Ordered list
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Paragraphs (double newline)
  html = html.split('\n\n').map(para => {
    if (para.startsWith('<')) return para;
    return `<p>${para.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── UTILITIES ────────────────────────────────────────────────────────────
function scrollToBottom() {
  const container = document.querySelector('.chat-container');
  container.scrollTop = container.scrollHeight;
}

function clearChatUI() {
  messagesEl.innerHTML = '';
  welcomeScreen.style.display = 'flex';
}

function autoResize() {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 180) + 'px';
}

function updateCharCount() {
  const len = messageInput.value.length;
  charCount.textContent = `${len} / 4000`;
  charCount.classList.toggle('warning', len > 3000 && len <= 3800);
  charCount.classList.toggle('danger', len > 3800);
  sendBtn.disabled = len === 0 || isLoading;
}

// ─── EVENT BINDING ────────────────────────────────────────────────────────
function bindEvents() {
  // Input events
  messageInput.addEventListener('input', () => { autoResize(); updateCharCount(); });

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage(messageInput.value);
    }
  });

  sendBtn.addEventListener('click', () => {
    if (!sendBtn.disabled) sendMessage(messageInput.value);
  });

  // Suggestion chips
  suggestionChips.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      messageInput.value = chip.textContent;
      autoResize();
      updateCharCount();
      messageInput.focus();
    });
  });

  // New session
  $('newChatBtn').addEventListener('click', () => {
    startNewSession();
    messageInput.focus();
  });

  // Sidebar toggle
  sidebarToggle.addEventListener('click', () => {
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      document.body.classList.toggle('sidebar-open');
    } else {
      document.body.classList.toggle('sidebar-collapsed');
    }
  });

  // Close sidebar on mobile when clicking outside
  document.querySelector('.main').addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      document.body.classList.remove('sidebar-open');
    }
  });

  // Profile panel
  profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = profilePanel.classList.toggle('visible');
    panelOverlay.classList.toggle('visible', open);
    profileBtn.classList.toggle('open', open);
  });

  panelOverlay.addEventListener('click', closePanel);

  $('switchUserBtn').addEventListener('click', () => {
    closePanel();
    localStorage.removeItem('ct_username');
    window.location.href = '/';
  });

  $('clearAllBtn').addEventListener('click', () => {
    closePanel();
    if (confirm('Clear ALL chat history and data? This cannot be undone.')) {
      localStorage.removeItem(STORAGE_KEY);
      sessions = {};
      startNewSession();
    }
  });

  // Reset button
  $('resetBtn').addEventListener('click', () => {
    resetModal.classList.add('visible');
  });

  $('resetCancel').addEventListener('click', () => {
    resetModal.classList.remove('visible');
  });

  $('resetConfirm').addEventListener('click', () => {
    resetModal.classList.remove('visible');
    // Reset current session messages but keep it
    if (sessions[currentSessionId]) {
      sessions[currentSessionId].messages = [];
      sessions[currentSessionId].title = 'New Session';
      persistSessions();
    }
    clearChatUI();
    renderHistoryList();
    sessionLabel.textContent = 'New Session';
  });

  resetModal.addEventListener('click', (e) => {
    if (e.target === resetModal) resetModal.classList.remove('visible');
  });

  // Focus input on load
  messageInput.focus();
}

function closePanel() {
  profilePanel.classList.remove('visible');
  panelOverlay.classList.remove('visible');
  profileBtn.classList.remove('open');
}

// ─── START ────────────────────────────────────────────────────────────────
init();

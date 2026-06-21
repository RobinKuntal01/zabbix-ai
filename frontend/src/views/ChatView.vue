<template>
  <div class="app" id="appRoot" :data-theme="theme">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-dot"><span>AC</span></div>
          <span class="brand-name">Aloo Chaat</span>
        </div>
        <button class="new-chat-btn" @click="newChat">
          <i class="ti ti-plus" aria-hidden="true"></i>
          New chat
        </button>
      </div>

      <div class="chat-list">
        <div v-if="sidebarChats.length === 0" class="no-chats-msg" style="padding:15px; font-size:13px; opacity:0.6; text-align:center;">
          No recent chats
        </div>
        <template v-else>
          <div class="sidebar-section">
            <div class="section-label">Recent Conversations</div>
          </div>
          <div 
            v-for="chat in sidebarChats" 
            :key="chat.session_id" 
            class="chat-item" 
            :class="{ active: currentSessionId === chat.session_id }"
            @click="switchChatSession(chat.session_id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.7; margin-right:8px; flex-shrink:0;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span class="chat-title">{{ chat.title }}</span>
          </div>
        </template>
      </div>

      <div class="sidebar-footer">
        <div class="user-pill">
          <div class="avatar">RB</div>
          <span class="user-name">Robin</span>
          <i class="ti ti-dots" style="font-size:15px;color:var(--color-text-tertiary)" aria-hidden="true"></i>
        </div>
      </div>
    </div>

    <!-- Main -->
    <div class="main">
      <div class="topbar">
        <div class="model-selector">
          <div class="model-dot"></div>
          Mistral 7B
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
        <div class="topbar-actions">
          <!-- Router Link to Agent Viewer -->
          <router-link to="/agent" class="icon-btn" title="ReAct Agent trace viewer" style="text-decoration:none;">
            <i class="ti ti-terminal" style="font-size: 18px;"></i>
          </router-link>
          <!-- Router Link to Upload -->
          <router-link to="/add-dox" class="icon-btn" title="Upload documents" style="text-decoration:none;">
            <i class="ti ti-file-upload" style="font-size: 18px;"></i>
          </router-link>
          <button class="icon-btn theme-btn" title="Toggle Dark/Light Mode" aria-label="Toggle theme" @click="toggleTheme">
            <svg v-if="theme === 'light'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
          </button>
          <button class="icon-btn" title="Search chats" aria-label="Search chats">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </button>
          <button class="icon-btn" title="Share" aria-label="Share conversation">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" x2="12" y1="2" y2="15"/></svg>
          </button>
        </div>
      </div>

      <!-- Chat messages -->
      <div class="chat-area" ref="chatAreaRef">
        <div class="divider-date"><span>Messages</span></div>

        <!-- Render Messages -->
        <div v-for="(msg, idx) in messages" :key="idx" class="message-group">
          <div :class="['msg-avatar', msg.role === 'bot' ? 'bot' : 'user']">
            {{ msg.role === 'bot' ? '✦' : 'RB' }}
          </div>
          <div class="msg-body">
            <div class="msg-sender">
              {{ msg.role === 'bot' ? 'Aloo Chaat' : 'You' }}
              <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <!-- Bot message has raw HTML formatting from LLM response -->
            <div v-if="msg.role === 'bot'" class="msg-content" v-html="msg.text"></div>
            <!-- User message is plain text -->
            <div v-else class="msg-content user-msg">{{ msg.text }}</div>
            
            <!-- Actions for bot replies -->
            <div v-if="msg.role === 'bot'" class="msg-actions">
              <button class="action-chip" @click="copyText(msg.text)"><i class="ti ti-copy" aria-hidden="true"></i>Copy</button>
              <button class="action-chip"><i class="ti ti-thumb-up" aria-hidden="true"></i>Good</button>
              <button class="action-chip" @click="retryMessage(idx)"><i class="ti ti-refresh" aria-hidden="true"></i>Retry</button>
            </div>
          </div>
        </div>

        <!-- Typing Indicator -->
        <div v-if="loading" class="typing-group">
          <div class="msg-avatar bot" aria-hidden="true">✦</div>
          <div>
            <div class="msg-sender" style="margin-bottom:4px;">Aloo Chaat</div>
            <div class="typing-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Suggested prompts -->
      <div class="suggested">
        <button class="suggested-chip" @click="insertPrompt('Check PROD3 CPU')"><i class="ti ti-activity" aria-hidden="true"></i>Check PROD3 CPU</button>
        <button class="suggested-chip" @click="insertPrompt('Raise a ticket')"><i class="ti ti-alert-triangle" aria-hidden="true"></i>Raise a ticket</button>
        <button class="suggested-chip" @click="insertPrompt('Cooling SOP')"><i class="ti ti-temperature" aria-hidden="true"></i>Cooling SOP</button>
      </div>

      <!-- Input area -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea 
            class="message-input" 
            ref="inputRef"
            v-model="inputText"
            @input="adjustHeight"
            @keydown.enter.prevent="handleEnter"
            rows="1" 
            placeholder="Ask about servers, racks, SLAs…" 
            aria-label="Chat message"
            :disabled="loading"
          ></textarea>
          <div class="input-actions">
            <button class="attach-btn" title="Attach file" aria-label="Attach file"><i class="ti ti-paperclip" aria-hidden="true"></i></button>
            <button class="send-btn" :disabled="loading || !inputText.trim()" @click="handleSend" aria-label="Send message">
              <i class="ti ti-arrow-up" aria-hidden="true"></i>
            </button>
          </div>
        </div>
        <div class="input-footer">
          <span>Press <kbd>Enter</kbd> to send &nbsp;·&nbsp; <kbd>Shift+Enter</kbd> for new line</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import {apiRequest} from '../utils/api'

const theme = ref('light')
const currentSessionId = ref('')
const sidebarChats = ref([])
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const chatAreaRef = ref(null)
const inputRef = ref(null)

function generateSessionId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function formatTime(timestamp) {
  const date = timestamp ? new Date(timestamp * 1000) : new Date();
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function loadSidebarChats(loadFirstChat = true) {
  try {
    const data = await apiRequest('/sidebar');
    sidebarChats.value = Array.isArray(data) ? data : [];

    if (loadFirstChat && sidebarChats.value.length > 0) {
      switchChatSession(sidebarChats.value[0].session_id);
    } else if (loadFirstChat && sidebarChats.value.length === 0) {
      newChat();
    }
  } catch (error) {
    console.error('Error loading sidebar chats:', error);
  }
}

async function loadChatHistory(sessionId) {
  if (!sessionId) return;

  currentSessionId.value = sessionId;
  try {
    const data = await apiRequest(`/chat-history/${encodeURIComponent(sessionId)}`);
    messages.value = Array.isArray(data)
      ? data.map((msg) => ({
          role: msg.role || 'bot',
          text: msg.text || '',
          timestamp: msg.timestamp || Date.now() / 1000,
        }))
      : [];
    scrollToBottom();
  } catch (error) {
    console.error('Error loading chat history:', error);
    messages.value = [];
  }
}

function switchChatSession(sessionId) {
  loadChatHistory(sessionId);
}

function newChat() {
  currentSessionId.value = generateSessionId();
  messages.value = [
    {
      role: 'bot',
      text: 'Hello! Started a fresh session. Ask me anything about servers, racks, or SLAs.',
      timestamp: Date.now() / 1000
    }
  ];
  loadSidebarChats(false);
  scrollToBottom();
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus();
    }
  });
}

function toggleTheme() {
  theme.value = theme.value === 'light' ? 'dark' : 'light';
}

function insertPrompt(text) {
  inputText.value = text;
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus();
      adjustHeight();
    }
  });
}

function adjustHeight() {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto';
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 120) + 'px';
  }
}

function handleEnter(e) {
  if (!e.shiftKey) {
    handleSend();
  }
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text || loading.value) return;

  // Add user message
  messages.value.push({
    role: 'user',
    text: text,
    timestamp: Date.now() / 1000
  });

  inputText.value = '';
  adjustHeight();
  scrollToBottom();

  loading.value = true;

  if (!currentSessionId.value) {
    currentSessionId.value = generateSessionId();
  }

  try {
    const data = await apiRequest('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: text,
        session_id: currentSessionId.value
      })
    });

    messages.value.push({
      role: 'bot',
      text: data.reply,
      timestamp: Date.now() / 1000
    });
    
    // Refresh sidebar to include this chat or update its title/timestamp
    loadSidebarChats(false);
  } catch (error) {
    messages.value.push({
      role: 'bot',
      text: "Sorry, there was an error processing your request.",
      timestamp: Date.now() / 1000
    });
  } finally {
    loading.value = false;
    scrollToBottom();
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.focus();
      }
    });
  }
}

function copyText(text) {
  navigator.clipboard.writeText(text);
}

function retryMessage(idx) {
  // Find the user message before this bot message
  let lastUserMsg = '';
  for (let i = idx - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') {
      lastUserMsg = messages.value[i].text;
      break;
    }
  }
  if (lastUserMsg) {
    inputText.value = lastUserMsg;
    handleSend();
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight;
    }
  });
}

onMounted(() => {
  loadSidebarChats(true);
});
</script>

<style scoped>
/* ── Design Tokens / CSS Variables ── */
.app {
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f9fafb;
  --color-bg-tertiary: #f3f4f6;
  --color-text-primary: #111827;
  --color-text-secondary: #4b5563;
  --color-text-tertiary: #9ca3af;
  --color-border: rgba(0, 0, 0, 0.08);
  --color-border-strong: rgba(0, 0, 0, 0.15);
  --brand-purple: #7c3aed;
  --brand-purple-hover: #6d28d9;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  
  display: flex;
  height: 100vh;
  width: 100%;
  font-family: 'DM Sans', sans-serif;
  background: var(--color-bg-primary);
  overflow: hidden;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: background 0.2s, color 0.2s;
}

.app[data-theme="dark"] {
  --color-bg-primary: #0f1115;
  --color-bg-secondary: #161920;
  --color-bg-tertiary: #212631;
  --color-text-primary: #f9fafb;
  --color-text-secondary: #9ca3af;
  --color-text-tertiary: #6b7280;
  --color-border: rgba(255, 255, 255, 0.08);
  --color-border-strong: rgba(255, 255, 255, 0.18);
}

/* ── Sidebar ── */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
}

.sidebar-header {
  padding: 16px 14px 12px;
  border-bottom: 1px solid var(--color-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.brand-dot {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-dot span {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: #a78bfa;
  letter-spacing: -0.5px;
}

.brand-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 100%;
  padding: 8px 10px;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border-strong);
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.new-chat-btn:hover {
  background: var(--color-bg-tertiary);
}

.new-chat-btn i { font-size: 15px; color: var(--color-text-secondary); }

.sidebar-section {
  padding: 12px 10px 4px;
}

.section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  padding: 0 4px;
  margin-bottom: 4px;
}

.chat-list { flex: 1; overflow-y: auto; padding-bottom: 8px; }

.chat-item {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  cursor: pointer;
  border-bottom: 1px solid transparent;
  transition: background 0.1s;
  position: relative;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.chat-item:hover { background: var(--color-bg-tertiary); }

.chat-item.active {
  background: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
  border-top: 1px solid var(--color-border);
}

.chat-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--brand-purple);
}

.chat-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.sidebar-footer {
  padding: 10px;
  border-top: 1px solid var(--color-border);
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}

.user-pill:hover { 
  background: var(--color-bg-tertiary); 
  border-color: var(--color-border);
}

.avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: #a78bfa;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.user-name { font-size: 12.5px; font-weight: 500; color: var(--color-text-primary); flex: 1; }

/* ── Main ── */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ── Topbar ── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  background: var(--color-bg-primary);
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border-strong);
  background: var(--color-bg-secondary);
  cursor: pointer;
  font-size: 12.5px;
  color: var(--color-text-primary);
  font-weight: 500;
  transition: background 0.15s;
}

.model-selector:hover { background: var(--color-bg-tertiary); }
.model-selector i { font-size: 14px; color: var(--color-text-secondary); }

.model-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
}

.topbar-actions { display: flex; gap: 6px; align-items: center; }

.icon-btn {
  width: 30px;
  height: 30px;
  border-radius: var(--border-radius-md);
  border: 1px solid transparent;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-secondary); 
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.icon-btn:hover { 
  background: var(--color-bg-secondary); 
  color: var(--color-text-primary); 
  border-color: var(--color-border);
}

/* ── Chat area ── */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
  scroll-behavior: smooth;
  background: var(--color-bg-primary);
}

.chat-area::-webkit-scrollbar { width: 6px; }
.chat-area::-webkit-scrollbar-thumb { background: var(--color-border-strong); border-radius: 3px; }

.message-group {
  display: flex;
  gap: 12px;
  padding: 8px 20px;
  max-width: 780px;
  margin: 0 auto;
  animation: fadeSlideIn 0.2s ease both;
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  margin-top: 2px;
  border: 1px solid var(--color-border);
}

.msg-avatar.user {
  background: #1a1a2e;
  color: #a78bfa;
  font-family: 'DM Mono', monospace;
  font-size: 9px;
}

.msg-avatar.bot {
  background: var(--color-bg-secondary);
  color: var(--brand-purple);
  font-size: 13px;
}

.msg-body { flex: 1; min-width: 0; }

.msg-sender {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.msg-time {
  font-size: 10px;
  color: var(--color-text-tertiary);
  font-weight: 400;
}

.msg-content {
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-primary);
}

.msg-content :deep(strong) {
  font-weight: 600;
}

.msg-content.user-msg {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-strong);
  border-radius: 4px 14px 14px 14px;
  padding: 10px 14px;
  display: inline-block;
  max-width: 85%;
}

.msg-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.15s;
}

.message-group:hover .msg-actions { opacity: 1; }

.action-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-primary);
  color: var(--color-text-secondary);
  font-size: 11px;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}

.action-chip:hover { 
  background: var(--color-bg-secondary); 
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}
.action-chip i { font-size: 13px; }

.divider-date {
  text-align: center;
  margin: 16px 0;
  position: relative;
}

.divider-date::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 20px;
  right: 20px;
  height: 1px;
  background: var(--color-border);
}

.divider-date span {
  position: relative;
  background: var(--color-bg-primary);
  padding: 0 10px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

/* ── Typing indicator ── */
.typing-group { display: flex; gap: 12px; padding: 6px 20px; max-width: 780px; margin: 0 auto; }

.typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  border-radius: 4px 14px 14px 14px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.typing-dots span {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--color-text-tertiary);
  animation: bounce 1.2s ease-in-out infinite;
}

.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

/* ── Input area ── */
.input-area {
  padding: 14px 20px 16px;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
  background: var(--color-bg-primary);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-strong);
  border-radius: 14px;
  padding: 8px 10px 8px 14px;
  transition: border-color 0.2s;
  max-width: 780px;
  margin: 0 auto;
}

.input-wrapper:focus-within {
  border-color: var(--brand-purple);
}

.message-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--color-text-primary);
  resize: none;
  min-height: 24px;
  max-height: 120px;
  overflow-y: auto;
  line-height: 1.5;
  padding: 2px 0;
}

.message-input::placeholder { color: var(--color-text-tertiary); }

.input-actions { display: flex; align-items: center; gap: 4px; }

.attach-btn {
  width: 30px; height: 30px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: color 0.15s, background 0.15s, border-color 0.15s;
}

.attach-btn:hover { 
  color: var(--color-text-secondary); 
  background: var(--color-bg-tertiary);
  border-color: var(--color-border);
}
.attach-btn i { font-size: 16px; }

.send-btn {
  width: 32px; height: 32px;
  border-radius: 9px;
  border: none;
  background: var(--brand-purple);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #fff;
  transition: background 0.15s, transform 0.1s;
  flex-shrink: 0;
}

.send-btn:hover { background: var(--brand-purple-hover); }
.send-btn:active { transform: scale(0.95); }
.send-btn i { font-size: 15px; }

.send-btn:disabled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

.input-footer {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.input-footer span {
  font-size: 10.5px;
  color: var(--color-text-tertiary);
}

.input-footer kbd {
  font-family: 'DM Mono', monospace;
  font-size: 9.5px;
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid var(--color-border-strong);
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
}

/* ── Suggested prompts ── */
.suggested {
  padding: 8px 20px 0;
  max-width: 780px;
  margin: 0 auto;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  background: var(--color-bg-primary);
}

.suggested-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid var(--color-border-strong);
  background: var(--color-bg-primary);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.1s, color 0.1s, border-color 0.1s;
  white-space: nowrap;
}

.suggested-chip:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border-color: var(--brand-purple);
}

.suggested-chip i { font-size: 13px; color: var(--brand-purple); }
</style>

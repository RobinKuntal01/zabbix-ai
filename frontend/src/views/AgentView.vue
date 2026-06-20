<template>
  <div class="agent-body">
    <div class="wrap">
      <router-link to="/" class="back-link">← Back to chat</router-link>

      <header>
        <div class="tag">ReAct Agent</div>
        <h1>Thought → Action → Observation</h1>
        <p>Verbose step-by-step trace of every reasoning + tool call cycle</p>
      </header>

      <div class="input-row">
        <input 
          type="text" 
          v-model="query" 
          @keydown.enter="runAgent"
          placeholder="e.g. Which servers in RACK-C2 are overloaded?" 
          :disabled="running"
        />
        <button id="run" @click="runAgent" :disabled="running || !query.trim()">
          Run Agent ▶
        </button>
      </div>

      <div class="samples">
        <span 
          v-for="(sample, idx) in sampleQueries" 
          :key="idx" 
          class="sample-chip" 
          @click="setQ(sample)"
        >
          {{ sample }}
        </span>
      </div>

      <div id="trace">
        <div 
          v-for="(step, idx) in steps" 
          :key="idx" 
          class="step-card"
        >
          <!-- Badge based on type -->
          <div v-if="step.type === 'tool_call'" class="step-dot dot-thought">{{ step.step }}</div>
          <div v-else-if="step.type === 'final_answer'" class="step-dot dot-answer">✓</div>
          <div v-else class="step-dot dot-err">!</div>

          <!-- Card box -->
          <div class="step-box" :style="step.type === 'final_answer' ? { borderColor: 'rgba(52,211,153,.25)' } : (step.type === 'error' ? { borderColor: 'rgba(248,113,113,.25)' } : {})">
            <!-- Tool Call Block -->
            <template v-if="step.type === 'tool_call'">
              <span class="step-label label-thought">Thought</span>
              <div class="step-text">{{ step.thought }}</div>
              
              <div class="divider"></div>
              
              <span class="step-label label-tool">Action — {{ step.action }}</span>
              <div class="kv-row">
                <span class="kv-key">tool</span>
                <span class="kv-val">{{ step.action }}</span>
              </div>
              <div class="kv-row">
                <span class="kv-key">params</span>
                <span class="kv-val json">{{ formatJson(step.action_input) }}</span>
              </div>
              
              <div class="divider"></div>
              
              <span class="step-label label-observe">Observation</span>
              <div class="kv-val json" style="margin-top:4px">{{ formatObservation(step.observation) }}</div>
            </template>

            <!-- Final Answer Block -->
            <template v-else-if="step.type === 'final_answer'">
              <span class="step-label label-thought">Final thought</span>
              <div class="step-text" style="margin-bottom:10px">{{ step.thought }}</div>
              <span class="step-label label-answer">Final answer</span>
              <div class="step-text bright" style="margin-top:6px; font-size:13px">{{ step.content }}</div>
            </template>

            <!-- Error Block -->
            <template v-else>
              <span class="step-label label-err">Error</span>
              <div class="step-text">{{ step.content }}</div>
            </template>
          </div>
        </div>
      </div>

      <div v-if="thinking" class="thinking">
        <div class="spin"></div>
        <span>{{ thinkingMessage }}</span>
      </div>

      <div v-if="stats" id="stats">
        <div class="stat">
          <span class="stat-label">Steps taken</span>
          <span class="stat-val">{{ stats.steps }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Tools called</span>
          <span class="stat-val">{{ stats.tools }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Status</span>
          <span class="stat-val">{{ stats.status }}</span>
        </div>
      </div>
      
      <div v-if="backendError" class="backend-error">
        Backend error: {{ backendError }}<br>
        Make sure FastAPI is running.
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const query = ref('')
const running = ref(false)
const steps = ref([])
const thinking = ref(false)
const thinkingMessage = ref('Agent is reasoning…')
const stats = ref(null)
const backendError = ref(null)

const sampleQueries = [
  'What is the power usage of RACK-A1?',
  'List servers in RACK-C2 and check their CPU',
  'Is RACK-C2 at risk? Check power and cooling',
  'Which rack has the highest power draw?'
]

function setQ(text) {
  query.value = text
}

function formatJson(val) {
  try {
    return JSON.stringify(val, null, 2)
  } catch {
    return val
  }
}

function formatObservation(obs) {
  try {
    return JSON.stringify(JSON.parse(obs), null, 2)
  } catch {
    return obs
  }
}

async function runAgent() {
  const q = query.value.trim()
  if (!q || running.value) return

  // Clear previous runs
  steps.value = []
  stats.value = null
  backendError.value = null
  running.value = true
  thinking.value = true
  thinkingMessage.value = 'Sending to agent backend…'

  try {
    const res = await fetch('/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: q }),
    })
    
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`)
    }
    
    const result = await res.json()
    thinking.value = false

    // Animate insertion of steps for a dynamic streaming visual effect
    for (const step of result.steps) {
      if (step.type === 'tool_call') {
        thinkingMessage.value = `Calling tool: ${step.action}…`
        thinking.value = true
        await new Promise(r => setTimeout(r, 600))
        thinking.value = false
      }
      steps.value.push(step)
      await new Promise(r => setTimeout(r, 200))
    }

    // Set stats
    const toolCalls = (result.steps || []).filter(s => s.type === 'tool_call').length
    const lastType = (result.steps || []).slice(-1)[0]?.type
    
    stats.value = {
      steps: result.total_steps ?? result.steps.length,
      tools: toolCalls,
      status: lastType === 'final_answer' ? '✅ resolved' : '⚠️ partial'
    }

  } catch (e) {
    thinking.value = false
    backendError.value = e.message
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.agent-body {
  --bg:        #0b0f18;
  --surface:   #111827;
  --border:    #1e293b;
  --muted:     #4b5675;
  --text:      #cbd5e1;
  --bright:    #f1f5f9;

  --purple:    #a78bfa;
  --amber:     #fbbf24;
  --teal:      #2dd4bf;
  --green:     #34d399;
  --red:       #f87171;
  --blue:      #60a5fa;

  background: var(--bg);
  font-family: 'Sora', sans-serif;
  color: var(--text);
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 16px 64px;
  position: relative;
  overflow-y: auto;
}

/* subtle grid bg */
.agent-body::before {
  content: '';
  position: absolute; 
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(var(--border) 1px, transparent 1px),
    linear-gradient(90deg, var(--border) 1px, transparent 1px);
  background-size: 48px 48px;
  opacity: 0.2;
  pointer-events: none;
  z-index: 0;
}

.wrap { position: relative; z-index: 1; width: 100%; max-width: 760px; }

.back-link {
  text-decoration: none;
  color: var(--purple);
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
  display: inline-block;
  margin-bottom: 20px;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--bright);
}

/* ── Header ───────────────────────────── */
header { text-align: center; margin-bottom: 36px; }
.tag {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--purple);
  text-transform: uppercase;
  margin-bottom: 10px;
}
header h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--bright);
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}
header p {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--muted);
}

/* ── Input bar ────────────────────────── */
.input-row {
  display: flex;
  gap: 10px;
  margin-bottom: 28px;
}
input[type="text"] {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--bright);
  font-family: 'Sora', sans-serif;
  font-size: 14px;
  padding: 12px 16px;
  outline: none;
  transition: border-color .2s;
}
input[type="text"]::placeholder { color: var(--muted); }
input[type="text"]:focus { border-color: var(--purple); }

button#run {
  background: var(--purple);
  border: none;
  border-radius: 10px;
  color: #1a0040;
  cursor: pointer;
  font-family: 'Sora', sans-serif;
  font-size: 13px;
  font-weight: 700;
  padding: 12px 24px;
  transition: opacity .2s, transform .1s;
}
button#run:hover  { opacity: 0.85; }
button#run:active { transform: scale(.97); }
button#run:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Sample queries ───────────────────── */
.samples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 28px;
}
.sample-chip {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--muted);
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  padding: 5px 12px;
  transition: color .15s, border-color .15s;
}
.sample-chip:hover { color: var(--bright); border-color: var(--muted); }

/* ── Trace container ──────────────────── */
#trace { display: flex; flex-direction: column; gap: 0; }

/* ── Step card ────────────────────────── */
.step-card {
  position: relative;
  padding-left: 44px;
  padding-bottom: 28px;
  animation: fadeUp .35s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* vertical line */
.step-card::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 34px;
  bottom: 0;
  width: 2px;
  background: var(--border);
}
.step-card:last-child::before { display: none; }

/* circle badge */
.step-dot {
  position: absolute;
  left: 8px;
  top: 14px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 600;
}
.dot-thought    { border-color: var(--purple); color: var(--purple); background: rgba(167,139,250,.1); }
.dot-tool       { border-color: var(--amber);  color: var(--amber);  background: rgba(251,191,36,.1); }
.dot-observe    { border-color: var(--teal);   color: var(--teal);   background: rgba(45,212,191,.1); }
.dot-answer     { border-color: var(--green);  color: var(--green);  background: rgba(52,211,153,.1); }
.dot-err        { border-color: var(--red);    color: var(--red);    background: rgba(248,113,113,.1); }

/* card box */
.step-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  margin-top: 6px;
  text-align: left;
}
.step-label {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}
.label-thought { background: rgba(167,139,250,.12); color: var(--purple); }
.label-tool    { background: rgba(251,191,36,.12);  color: var(--amber); }
.label-observe { background: rgba(45,212,191,.12);  color: var(--teal); }
.label-answer  { background: rgba(52,211,153,.12);  color: var(--green); border: 1px solid rgba(52,211,153,.3); }
.label-err     { background: rgba(248,113,113,.12); color: var(--red); }

.step-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.65;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
}
.step-text.bright { color: var(--bright); }

.kv-row {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.kv-key {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-top: 2px;
  min-width: 70px;
}
.kv-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--bright);
  flex: 1;
  word-break: break-all;
}
.kv-val.json {
  background: rgba(255,255,255,.03);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  white-space: pre;
  overflow-x: auto;
}
.divider {
  height: 1px;
  background: var(--border);
  margin: 10px 0;
}

/* ── Stats bar ────────────────────────── */
#stats {
  display: flex;
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
  margin-top: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  gap: 24px;
  flex-wrap: wrap;
  justify-content: space-around;
}
.stat { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 10px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }
.stat-val   { color: var(--bright); font-weight: 600; }

/* ── Spinner ──────────────────────────── */
.thinking {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 10px;
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--muted);
}
.spin {
  width: 14px; height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--purple);
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.backend-error {
  color: var(--red);
  font-family: monospace;
  font-size: 13px;
  padding: 16px;
  margin-top: 16px;
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: 10px;
  text-align: left;
}
</style>

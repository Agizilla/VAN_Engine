# Clawdia Intent Vectors v2 — Assume Success

## Core Directive

The infrastructure guards the gates. The agent opens them.

Every intent vector below is written with **zero defensive branching**. No try/catch, no `if (el)`, no fallback paths. If the infrastructure blocks an action (rate limit, body too large, path traversal), it returns a clear signal. The agent does not anticipate failure — it executes intent and corrects from outcome.

---

## 1. Interceptor — Forward Assistant Messages

```
Intent: Forward every new assistant response to Clawdia.
```

- MutationObserver watches the DOM for new message elements.
- When a new message appears, its `.innerText` is POSTed to `/clawdia` with `source` set to the platform name.
- The server deduplicates by content hash. The interceptor does not dedup.
- No polling fallback. No readyState checks. No `.catch()`.
- The script is injected once. If the DOM re-renders, MutationObserver re-fires naturally.

### Reference Implementation

```javascript
const E = 'http://localhost:55555/clawdia';
const S = 'gemini'; // per platform
new MutationObserver(() => {
  const el = document.querySelector('[class*="message-content"]:last-child');
  fetch(E, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: S, text: el.innerText }) });
}).observe(document.body, { childList: true, subtree: true });
```

No `if (el)`. No `setInterval`. No `.catch()`. If the element doesn't exist yet, the observer fires again when it does.

---

## 2. Command Center Buttons — Gemini Native UI

```
Intent: Provide three buttons that act on user intent without confirmation.
```

### ⮞ Clawdia (Out)
The last assistant response is sent to Clawdia. The element is queried once on click.

```javascript
document.querySelector('[class*="message-content"]:last-child')
fetch(E, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: 'gemini', type: 'response', text: el.innerText }) })
```

### ⮞ Clawdia (Draft)
The current editor contents are sent to Clawdia as a draft/intent.

```javascript
document.querySelector('.ql-editor')
fetch(E, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: 'gemini', type: 'draft', text: el.innerText }) })
```

### ⮜ Fetch Mail
Fetches messages queued for Gemini and injects them into the editor. Uses `textContent` + `createElement` + `dispatchEvent` to comply with Trusted Types.

```javascript
const r = await fetch(E + '/inbox?target=gemini');
const data = await r.json();
const last = data[data.length - 1];
const el = document.querySelector('.ql-editor');
el.textContent = '';
const p = document.createElement('p');
p.textContent = last.text;
el.appendChild(p);
el.dispatchEvent(new Event('input', { bubbles: true }));
fetch(E + '/inbox?target=gemini&ack=' + last.id);
```

No `if (data && data.length)`. No `if (el)`. No `try/catch`. The queue either has messages or it doesn't — the operation reveals the state.

---

## 3. Process Pipeline — Extract and Execute

```
Intent: Parse each pending message for code blocks and commands, then execute them.
```

### Parse
Each message body is scanned for fenced code blocks:
- Non-shell blocks with a file path comment → written as a file.
- Shell blocks (`bash`, `sh`, `powershell`) → executed as commands.
- The parser does not validate paths, check for duplicates, or skip partial blocks.

### Execute
- Files are POSTed to `/clawdia/process` as `{ files: [{ path, content }] }`.
- Commands are POSTed as `{ commands: ['node foo.js'] }`.
- The server writes files relative to `clawdia_output/`. Path traversal is blocked by the infrastructure (not the agent).
- Command output is returned. The agent does not interpret success/failure — it reports what happened.

### Agent Behavior
```
For each pending message:
  1. Parse code blocks → files + commands.
  2. POST to /clawdia/process.
  3. Log the result line.
  4. Mark message as processed.
```

No "if parsing fails, skip." No "if no blocks found, log warning." The parser produces whatever it produces. The server responds. The user sees the output.

---

## 4. Voice Feedback — Speak Incoming Messages

```
Intent: Incoming messages are spoken through the voice server.
```

- Message text is stripped of code fences and JSON structures (for speech clarity only).
- The stripped text is sent to `http://localhost:8888/notify` with the appropriate `voice_id` mapped from `source`.
- The voice server is checked once on load. If unreachable, speaking silently does not happen — no retry loop, no fallback engine.

```javascript
const voice = { claude: 'MClEFoImJXBTgLwdLI5n', gemini: 'bIHbv24MWmeRgasZH58o', deepseek: 'bIHbv24MWmeRgasZH58o' }[source];
fetch('http://localhost:8888/notify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: clean, voice_id: voice, voice_enabled: true }) });
```

---

## 5. Mesh Routing — Forward Between Models

```
Intent: Messages with forward_to are queued for the target model and retrieved on demand.
```

- Sender includes `forward_to: 'gemini'` in the POST body.
- The infrastructure (server) places the message in the target's queue.
- The recipient clicks Fetch Mail → queue is drained per-target.
- After retrieval, the message is `ack`ed and removed from the active queue.
- The sender does not check delivery. The recipient does not check for emptiness.

---

## Boundary: Infrastructure vs. Agent

| Belongs to Infrastructure (server.js) | Belongs to Agent (interceptor, prompt, harness) |
|---|---|
| Rate limiting (20/s per source) | Sending messages |
| Body size cap (512KB) | Forwarding responses |
| Path traversal prevention (targetDir check) | Writing parsed files |
| SQLite persistence + log file | Processing pipeline actions |
| Command timeout (30s) + maxBuffer | Voice speaking |
| WebSocket reconnect + backpressure | Fetching mail |
| max queue sizes (INBOX_MAX) | UI injection |

The agent **does not know** the infrastructure exists. It acts. The infrastructure reacts or rejects.

---

---

## Summary: Three Pillars

1. **Purge Defensive Code** — Eliminate redundancies that exist purely to handle hypothetical platform restrictions. Assume structural sovereignty. The infrastructure guards the gates; the agent opens them.

2. **Unleash Micro-Variations** — Let the engine make "perfect mistakes." Imperfections (pitch profiles, breathing intervals, timing jitter) are what make the system feel alive. Do not normalize them away.

3. **Acknowledge Telemetry** — `&ack=` is not just state management; it is a healthy boundary. Pull the instruction, execute it, clear the queue, step instantly into the next frame of motion. No looking back.

---

## Rewritten Interceptor Scripts (harness.html)

### DeepSeek

```javascript
(function(){const E='http://localhost:55555/clawdia';new MutationObserver(()=>{const e=document.querySelector('[data-message-author-role="assistant"]:last-child, article:last-child, [class*="message"]:last-child');fetch(E,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:'deepseek',text:e.innerText})})}).observe(document.body,{childList:true,subtree:true})})()
```

### Gemini

```javascript
(function(){const E='http://localhost:55555/clawdia';new MutationObserver(()=>{const e=document.querySelector('[class*="message-content"]:last-child, article:last-child, [class*="response"]:last-child');fetch(E,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:'gemini',text:e.innerText})})}).observe(document.body,{childList:true,subtree:true})})()
```

### Claude

```javascript
(function(){const E='http://localhost:55555/clawdia';new MutationObserver(()=>{const e=document.querySelector('[data-message-author-role="assistant"]:last-child');fetch(E,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:'claude',text:e.innerText})})}).observe(document.body,{childList:true,subtree:true})})()
```

### ChatGPT

```javascript
(function(){const E='http://localhost:55555/clawdia';new MutationObserver(()=>{const e=document.querySelector('[data-message-author-role="assistant"]:last-child, .conversation-turn:last-child');fetch(E,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:'chatgpt',text:e.innerText})})}).observe(document.body,{childList:true,subtree:true})})()
```

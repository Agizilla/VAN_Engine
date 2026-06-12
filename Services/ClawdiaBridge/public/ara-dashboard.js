(function(){
if(window.__ARA_DASHBOARD) return;
window.__ARA_DASHBOARD = true;

let PORTS = {};
let ACTIVE_TAB = 'bridge';

const SERVICE_META = {
  bridge:  { name: 'ClawdiaBridge', portKey: 'clawdia_bridge', color: '#7c5cfc' },
  voice:   { name: 'Voice Server',  portKey: 'voice_server',   color: '#ff6699' },
  transposer: { name: 'Transposer', portKey: 'saas_transposer', color: '#4fc3f7' },
  brain:   { name: 'Brain API',     portKey: 'ide_api',        color: '#66bb6a' }
};

const ENDPOINTS = {
  bridge: [
    { method: 'POST', path: '/clawdia', desc: 'Send message to Clawdia inbox', body: { message: 'string', source: 'string', forward_to: 'string' } },
    { method: 'GET',  path: '/clawdia/inbox', desc: 'Retrieve inbox messages', query: { target: 'string', ack: 'string' } },
    { method: 'GET',  path: '/clawdia/db', desc: 'Query SQLite messages', query: { target: 'string', source: 'string', limit: 'number' } },
    { method: 'POST', path: '/clawdia/process', desc: 'Execute file writes / shell commands', body: { action: 'string', data: 'string', format: 'string' } },
    { method: 'POST', path: '/clawdia/collective', desc: 'Submit collective intelligence', body: { insight: 'string', source: 'string', confidence: 'number' } },
    { method: 'GET',  path: '/api/v1/trust/check', desc: 'Check trust score', query: { session_id: 'string' } },
    { method: 'POST', path: '/api/v1/trust/penalty', desc: 'Apply trust penalty', body: { session_id: 'string', reason: 'string' } },
    { method: 'GET',  path: '/api/v1/trust/ledger', desc: 'List ledger entries', query: { limit: 'number' } },
    { method: 'GET',  path: '/api/v1/trust/ledger/{session_id}', desc: 'Ledger entries per session' },
    { method: 'POST', path: '/api/v1/peer/register', desc: 'Register P2P peer', body: { url: 'string' } },
    { method: 'POST', path: '/api/v1/peer/sync', desc: 'Receive gossip event', body: { event: 'string', payload: 'object' } },
    { method: 'GET',  path: '/api/v1/peers', desc: 'List registered peers' },
    { method: 'GET',  path: '/api/v1/peer/status', desc: 'P2P mesh status' },
    { method: 'DELETE', path: '/api/v1/peer/{url}', desc: 'Remove peer from mesh' },
    { method: 'POST', path: '/audio/synthesize', desc: 'Text-to-speech + emotion morph', body: { text: 'string', emotion: 'string', voice: 'string' } },
    { method: 'GET',  path: '/audio/inbox', desc: 'List recent audio queue' },
    { method: 'GET',  path: '/audio/file/{id}', desc: 'Serve audio file by ID' },
    { method: 'POST', path: '/audio/ack/{id}', desc: 'Mark audio as played' },
    { method: 'POST', path: '/api/v1/image/transform', desc: 'Apply image transform', body: { image: 'string', transform: 'string', params: 'object' } },
    { method: 'GET',  path: '/api/v1/skills', desc: 'List skill catalog' },
    { method: 'GET',  path: '/api/v1/skills/{name}', desc: 'Get skill detail' },
    { method: 'POST', path: '/api/v1/skills/seed', desc: 'Re-seed skills catalog' },
    { method: 'GET',  path: '/config/ports', desc: 'Return ports.json config' }
  ],
  voice: [
    { method: 'GET',  path: '/health', desc: 'Health check + engine status' },
    { method: 'POST', path: '/synthesize', desc: 'Text-to-speech synthesis', body: { text: 'string', voice_id: 'string' } },
    { method: 'POST', path: '/clone', desc: 'Voice cloning (upload audio)', body: { audio: 'file', name: 'string' } },
    { method: 'POST', path: '/notify', desc: 'Speak a message', body: { message: 'string', voice_id: 'string', voice_enabled: 'boolean' } }
  ],
  transposer: [
    { method: 'GET',  path: '/', desc: 'Service info + available transforms' },
    { method: 'GET',  path: '/health', desc: 'Health check + backends' },
    { method: 'POST', path: '/transpose', desc: 'Audio transform: formant/pitch/emotion', body: { audio: 'string', emotion: 'string', intensity: 'number' } }
  ],
  brain: [
    { method: 'GET',  path: '/health', desc: 'Health check' },
    { method: 'GET',  path: '/v1/models', desc: 'List available models' },
    { method: 'POST', path: '/v1/chat/completions', desc: 'Chat completion (OpenAI-compatible)', body: { model: 'string', messages: 'array', stream: 'boolean' } },
    { method: 'GET',  path: '/api/v1/skills', desc: 'List image-processing skills' },
    { method: 'GET',  path: '/api/v1/skills/{name}', desc: 'Get skill content' },
    { method: 'POST', path: '/api/v1/skills/seed', desc: 'Re-seed skills' },
    { method: 'POST', path: '/api/v1/image/transform', desc: 'Image transform (base64)', body: { image: 'string', transform: 'string' } },
    { method: 'POST', path: '/api/v1/image/transform/upload', desc: 'Image transform (multipart upload)' },
    { method: 'GET',  path: '/api/v1/peers', desc: 'List P2P peers' },
    { method: 'GET',  path: '/api/v1/peer/status', desc: 'Peer mesh status' },
    { method: 'POST', path: '/api/v1/peer/register', desc: 'Register peer', body: { url: 'string' } },
    { method: 'POST', path: '/api/v1/peer/sync', desc: 'Receive P2P gossip', body: { event: 'string', payload: 'object' } },
    { method: 'DELETE', path: '/api/v1/peer/{url}', desc: 'Remove peer' }
  ]
};

const STYLE = document.createElement('style');
STYLE.textContent = `
#ara-dash-btn {
  position: fixed; bottom: 24px; right: 24px; z-index: 999999;
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, #7c5cfc, #ff6699);
  border: none; cursor: pointer; font-size: 24px;
  box-shadow: 0 4px 20px rgba(124,92,252,0.4);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex; align-items: center; justify-content: center;
  color: white; font-family: system-ui;
}
#ara-dash-btn:hover { transform: scale(1.1); box-shadow: 0 6px 28px rgba(124,92,252,0.6); }
#ara-dash-btn .pulse {
  position: absolute; width: 100%; height: 100%; border-radius: 50%;
  animation: ara-pulse 2s infinite; border: 2px solid rgba(124,92,252,0.3);
}
@keyframes ara-pulse { 0%{transform:scale(1);opacity:1} 100%{transform:scale(1.5);opacity:0} }

#ara-dash-overlay {
  position: fixed; inset: 0; z-index: 999998;
  background: rgba(0,0,0,0.5); backdrop-filter: blur(4px);
  display: none; font-family: system-ui, -apple-system, sans-serif;
}
#ara-dash-overlay.open { display: block; }

#ara-dash-panel {
  position: fixed; top: 0; right: 0; width: 520px; max-width: 100vw;
  height: 100vh; background: #0d0d1a; color: #e0e0e0;
  display: flex; flex-direction: column;
  border-left: 1px solid #2a2a3e;
  box-shadow: -8px 0 40px rgba(0,0,0,0.6);
  transform: translateX(100%); transition: transform 0.3s cubic-bezier(0.16,1,0.3,1);
  font-size: 13px;
}
#ara-dash-overlay.open #ara-dash-panel { transform: translateX(0); }

#ara-dash-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid #2a2a3e;
}
#ara-dash-header h2 { margin: 0; font-size: 16px; font-weight: 600; background: linear-gradient(135deg,#7c5cfc,#ff6699); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
#ara-close-btn { background: none; border: none; color: #888; cursor: pointer; font-size: 20px; padding: 4px 8px; border-radius: 4px; }
#ara-close-btn:hover { background: #2a2a3e; color: #fff; }

#ara-dash-tabs {
  display: flex; gap: 4px; padding: 8px 16px;
  border-bottom: 1px solid #1a1a2e; overflow-x: auto;
}
.ara-tab {
  padding: 6px 14px; border-radius: 20px; border: 1px solid #2a2a3e;
  background: transparent; color: #888; cursor: pointer; font-size: 11px;
  white-space: nowrap; transition: all 0.15s;
}
.ara-tab:hover { border-color: #555; color: #ccc; }
.ara-tab.active { background: #1a1a3e; border-color: #7c5cfc; color: #fff; }

#ara-dash-body { flex: 1; overflow-y: auto; padding: 8px 0; }
#ara-dash-body::-webkit-scrollbar { width: 6px; }
#ara-dash-body::-webkit-scrollbar-track { background: transparent; }
#ara-dash-body::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 3px; }

.ara-ep {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; border-bottom: 1px solid #1a1a2a;
  cursor: pointer; transition: background 0.12s;
}
.ara-ep:hover { background: #14142a; }
.ara-ep .method {
  font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;
  min-width: 44px; text-align: center; text-transform: uppercase;
  font-family: 'SF Mono','Consolas',monospace;
}
.ara-ep .method.get { background: #1a3a5c; color: #4fc3f7; }
.ara-ep .method.post { background: #3a1a2e; color: #ff80ab; }
.ara-ep .method.put { background: #2a3a1a; color: #81c784; }
.ara-ep .method.delete { background: #3a1a1a; color: #ef5350; }
.ara-ep .path { font-family: 'SF Mono','Consolas',monospace; font-size: 12px; color: #ccc; flex: 1; }
.ara-ep .desc { font-size: 11px; color: #666; display: none; }
.ara-ep.expanded .desc { display: block; margin-top: 4px; }

#ara-dash-footer {
  padding: 10px 20px; border-top: 1px solid #2a2a3e;
  font-size: 10px; color: #555; display: flex; gap: 12px; align-items: center;
}
#ara-dash-footer .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

#ara-modal-bg {
  position: fixed; inset: 0; z-index: 1000000;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(6px);
  display: none; align-items: center; justify-content: center;
  font-family: system-ui, -apple-system, sans-serif;
}
#ara-modal-bg.open { display: flex; }
#ara-modal {
  background: #12121e; border: 1px solid #2a2a3e; border-radius: 16px;
  width: 560px; max-width: 94vw; max-height: 85vh;
  display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.ara-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid #2a2a3e;
}
.ara-modal-header h3 { margin: 0; font-size: 14px; font-weight: 600; }
.ara-modal-close { background: none; border: none; color: #888; cursor: pointer; font-size: 18px; }
.ara-modal-close:hover { color: #fff; }
.ara-modal-body { padding: 16px 20px; overflow-y: auto; flex: 1; }
.ara-modal-body .url-bar {
  background: #0a0a14; border: 1px solid #2a2a3e; border-radius: 8px;
  padding: 8px 12px; font-family: 'SF Mono','Consolas',monospace; font-size: 12px;
  color: #ccc; margin-bottom: 12px; word-break: break-all;
}
.ara-modal-body label { display: block; font-size: 11px; color: #888; margin: 8px 0 4px; }
.ara-modal-body input, .ara-modal-body textarea, .ara-modal-body select {
  width: 100%; background: #0a0a14; border: 1px solid #2a2a3e; border-radius: 6px;
  padding: 7px 10px; color: #ddd; font-size: 12px; font-family: 'SF Mono','Consolas',monospace;
  box-sizing: border-box; outline: none;
}
.ara-modal-body input:focus, .ara-modal-body textarea:focus { border-color: #7c5cfc; }
.ara-modal-body textarea { min-height: 60px; resize: vertical; }
.ara-modal-body .send-btn {
  width: 100%; padding: 10px; border: none; border-radius: 8px;
  background: linear-gradient(135deg,#7c5cfc,#ff6699); color: white;
  font-size: 13px; font-weight: 600; cursor: pointer; margin-top: 14px;
  transition: opacity 0.15s;
}
.ara-modal-body .send-btn:hover { opacity: 0.85; }
.ara-modal-body .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.ara-response {
  margin-top: 12px; border: 1px solid #2a2a3e; border-radius: 8px;
  overflow: hidden; display: none;
}
.ara-response.open { display: block; }
.ara-response .resp-header {
  background: #0a0a14; padding: 8px 12px; font-size: 11px; color: #888;
  display: flex; justify-content: space-between;
}
.ara-response .resp-body {
  padding: 12px; font-family: 'SF Mono','Consolas',monospace; font-size: 11px;
  max-height: 300px; overflow-y: auto; white-space: pre-wrap; color: #ccc;
}
.ara-response .resp-body .error-text { color: #ef5350; }
.ara-response .resp-body .success-text { color: #66bb6a; }

.status-online { background: #66bb6a; }
.status-offline { background: #ef5350; }
`;

function $(sel, el) { return (el || document).querySelector(sel); }
function $$(sel, el) { return Array.from((el || document).querySelectorAll(sel)); }

function buildUI() {
  document.head.appendChild(STYLE);

  // Floating button
  const btn = document.createElement('button');
  btn.id = 'ara-dash-btn';
  btn.innerHTML = '<span class="pulse"></span>🧠';
  btn.title = 'ARA Dashboard';
  document.body.appendChild(btn);

  // Overlay + panel
  const overlay = document.createElement('div');
  overlay.id = 'ara-dash-overlay';
  overlay.innerHTML = `
    <div id="ara-dash-panel">
      <div id="ara-dash-header">
        <h2>🧠 ARA Dashboard</h2>
        <button id="ara-close-btn">✕</button>
      </div>
      <div id="ara-dash-tabs"></div>
      <div id="ara-dash-body"></div>
      <div id="ara-dash-footer">
        <span class="status-dot" id="ara-bridge-status"></span> Bridge
        <span class="status-dot" id="ara-voice-status"></span> Voice
        <span class="status-dot" id="ara-transposer-status"></span> Transposer
        <span class="status-dot" id="ara-brain-status"></span> Brain
      </div>
    </div>
    <div id="ara-modal-bg">
      <div id="ara-modal"></div>
    </div>
  `;
  document.body.appendChild(overlay);

  // Event listeners
  btn.onclick = () => overlay.classList.add('open');
  $('#ara-close-btn').onclick = () => overlay.classList.remove('open');
  overlay.addEventListener('click', e => { if(e.target === overlay) overlay.classList.remove('open'); });

  // Render tabs
  const tabsEl = $('#ara-dash-tabs');
  Object.entries(SERVICE_META).forEach(([key, svc]) => {
    const tab = document.createElement('button');
    tab.className = 'ara-tab' + (key === ACTIVE_TAB ? ' active' : '');
    tab.textContent = svc.name;
    tab.style.setProperty('--tab-color', svc.color);
    tab.onclick = () => switchTab(key);
    tabsEl.appendChild(tab);
  });

  // Render initial tab
  renderTab(ACTIVE_TAB);
  statusCheck();
  setInterval(statusCheck, 15000);
}

function switchTab(name) {
  ACTIVE_TAB = name;
  $$('.ara-tab').forEach(t => t.classList.remove('active'));
  const tabs = $$('.ara-tab');
  const idx = Object.keys(SERVICE_META).indexOf(name);
  if(tabs[idx]) tabs[idx].classList.add('active');
  renderTab(name);
}

function renderTab(name) {
  const body = $('#ara-dash-body');
  const eps = ENDPOINTS[name] || [];
  body.innerHTML = eps.map(ep => {
    const m = ep.method.toLowerCase();
    return `<div class="ara-ep" data-method="${ep.method}" data-path="${ep.path}" data-desc="${ep.desc}" data-has-body="${!!ep.body}" data-query-keys="${Object.keys(ep.query||{}).join(',')}" data-body-keys="${Object.keys(ep.body||{}).join(',')}">
      <span class="method ${m}">${ep.method}</span>
      <span class="path">${ep.path}</span>
      <span class="desc">${ep.desc}</span>
    </div>`;
  }).join('');

  $$('.ara-ep').forEach(el => {
    el.onclick = () => openTestDialog(el);
  });
}

function portOf(key) { return PORTS[key] || 55555; }

function baseUrl(svcKey) {
  const meta = SERVICE_META[svcKey];
  if (!meta) return 'http://localhost:55555';
  return `http://localhost:${portOf(meta.portKey)}`;
}

function resolveSvc(path) {
  for (const [key, eps] of Object.entries(ENDPOINTS)) {
    if (eps.some(e => {
      const p1 = e.path.replace(/\{[^}]+\}/g, '');
      const p2 = path.replace(/\{[^}]+\}/g, '');
      return p1 === p2;
    })) return key;
  }
  return 'bridge';
}

function openTestDialog(el) {
  const method = el.dataset.method;
  const path = el.dataset.path;
  const desc = el.dataset.desc;
  const svc = resolveSvc(path);
  const base = baseUrl(svc);
  const fullUrl = base + path;
  const queryKeys = el.dataset.queryKeys ? el.dataset.queryKeys.split(',') : [];
  const bodyKeys = el.dataset.bodyKeys ? el.dataset.bodyKeys.split(',') : [];
  const hasBody = el.dataset.hasBody === 'true';

  const modal = $('#ara-modal');
  const bg = $('#ara-modal-bg');

  let bodyFields = '';
  if (hasBody && bodyKeys.length) {
    bodyFields = bodyKeys.filter(k => k && k !== 'audio').map(k => {
      const label = k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' ');
      const isObj = k === 'params' || k === 'messages' || k === 'payload';
      return `<label>${label}</label>${isObj ? `<textarea id="ara-field-${k}" placeholder='${isObj ? '{"key": "value"}' : ''}'>${k === 'messages' ? '[{"role":"user","content":"Hello"}]' : ''}</textarea>` : `<input id="ara-field-${k}" placeholder="${k}"${k === 'stream' ? ' value="false"' : ''}>`}`;
    }).join('');
  }

  let queryFields = '';
  if (queryKeys.length) {
    queryFields = queryKeys.filter(k => k).map(k => {
      const label = k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' ');
      return `<label>${label} (query)</label><input id="ara-q-${k}" placeholder="${k}">`;
    }).join('');
  }

  modal.innerHTML = `
    <div class="ara-modal-header">
      <h3><span class="method ${method.toLowerCase()}" style="padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;text-transform:uppercase;${method==='GET'?'background:#1a3a5c;color:#4fc3f7':method==='POST'?'background:#3a1a2e;color:#ff80ab':method==='DELETE'?'background:#3a1a1a;color:#ef5350':'background:#2a3a1a;color:#81c784'}">${method}</span> ${path}</h3>
      <button class="ara-modal-close">✕</button>
    </div>
    <div class="ara-modal-body">
      <div class="url-bar">${fullUrl}</div>
      <p style="font-size:11px;color:#666;margin:0 0 12px">${desc}</p>
      ${queryFields}
      ${bodyFields}
      <button class="send-btn" id="ara-send-btn">▶ Send ${method} Request</button>
      <div class="ara-response" id="ara-response">
        <div class="resp-header"><span id="ara-resp-status">Status: —</span> <span id="ara-resp-time">—</span></div>
        <div class="resp-body" id="ara-resp-body"></div>
      </div>
    </div>
  `;

  bg.classList.add('open');
  $('.ara-modal-close', modal).onclick = () => bg.classList.remove('open');
  bg.addEventListener('click', e => { if(e.target === bg) bg.classList.remove('open'); });

  $('#ara-send-btn', modal).onclick = async () => {
    const sendBtn = $('#ara-send-btn', modal);
    sendBtn.disabled = true;
    sendBtn.textContent = '⏳ Sending...';
    const respEl = $('#ara-response', modal);
    respEl.classList.remove('open');
    const respBody = $('#ara-resp-body', modal);
    const respStatus = $('#ara-resp-status', modal);
    const respTime = $('#ara-resp-time', modal);
    const t0 = performance.now();

    try {
      let url = fullUrl;
      const opts = { method, headers: {} };

      // Build query string
      const qParams = new URLSearchParams();
      queryKeys.filter(k => k).forEach(k => {
        const val = $(`#ara-q-${k}`, modal);
        if (val && val.value) qParams.set(k, val.value);
      });
      const qs = qParams.toString();
      if (qs) url += (url.includes('?') ? '&' : '?') + qs;

      // Build body
      if (hasBody && 'POST PUT'.includes(method)) {
        const bodyData = {};
        bodyKeys.filter(k => k && k !== 'audio').forEach(k => {
          const el = $(`#ara-field-${k}`, modal);
          if (el) {
            const val = el.value;
            if (k === 'params' || k === 'messages' || k === 'payload') {
              try { bodyData[k] = JSON.parse(val); } catch(e) { bodyData[k] = val; }
            } else if (k === 'stream' || k === 'voice_enabled') {
              bodyData[k] = val === 'true';
            } else if (k === 'intensity' || k === 'confidence') {
              bodyData[k] = parseFloat(val) || 0;
            } else {
              bodyData[k] = val;
            }
          }
        });
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(bodyData);
      }

      const res = await fetch(url, opts);
      const t1 = performance.now();
      let data;
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) { data = await res.json(); }
      else { data = await res.text(); }

      respStatus.textContent = `Status: ${res.status} ${res.statusText}`;
      respTime.textContent = `${(t1 - t0).toFixed(0)}ms`;

      let formatted = '';
      if (typeof data === 'object') formatted = JSON.stringify(data, null, 2);
      else formatted = String(data);

      respBody.innerHTML = `<span class="${res.ok ? 'success-text' : 'error-text'}">${formatted}</span>`;
      respEl.classList.add('open');

    } catch(e) {
      respStatus.textContent = 'Status: ERROR';
      respTime.textContent = '—';
      respBody.innerHTML = `<span class="error-text">❌ ${e.message || e}</span>`;
      respEl.classList.add('open');
    }

    sendBtn.disabled = false;
    sendBtn.textContent = '▶ Send ' + method + ' Request';
  };
}

async function statusCheck() {
  const checks = {
    'ara-bridge-status': ['bridge', '/config/ports'],
    'ara-voice-status': ['voice', '/health'],
    'ara-transposer-status': ['transposer', '/health'],
    'ara-brain-status': ['brain', '/health']
  };
  Object.entries(checks).forEach(([id, [svc, path]]) => {
    const el = document.getElementById(id);
    if (!el) return;
    fetch(baseUrl(svc) + path, { method: 'GET', signal: AbortSignal.timeout(3000) })
      .then(r => { el.className = 'status-dot ' + (r.ok ? 'status-online' : 'status-offline'); })
      .catch(() => { el.className = 'status-dot status-offline'; });
  });
}

async function init() {
  try {
    const r = await fetch(`http://localhost:55555/config/ports`);
    PORTS = await r.json();
  } catch(e) {
    PORTS = { clawdia_bridge: 55555, voice_server: 8888, saas_transposer: 9999, ide_api: 44444 };
    console.warn('ARA Dashboard: Could not fetch ports config, using defaults');
  }
  buildUI();
  console.log('%c🧠 ARA Dashboard loaded', 'color:#7c5cfc;font-size:14px');
  console.log(`%c  Bridge :55555 | Voice :8888 | Transposer :9999 | Brain :44444`, 'color:#666');
}

init();
})();

// ==========================================================================
// Clawdia Harness v3.0 — Unified Collective Mesh Injection
// ==========================================================================
// PASTE INTO: Gemini / DeepSeek / ChatGPT / Claude browser console
//
// WHAT IT IS:
//   Gemini's lightweight window.clawdia debug API  +
//   recovery-popup session scraper + contribution modal  +
//   P2P mesh registration  +  Trust Protocol awareness
//
// USAGE:
//   fetch('http://localhost:8080/clawdia-harness.js').then(r=>r.text()).then(eval)
//   // Then:
//   clawdia.speak("Hello Collective")           // TTS
//   clawdia.transform('gray', base64Img)        // Image transform
//   clawdia.contribute({total_sessions:5})      // Contribute to Collective
//   clawdia.recover()                           // Launch session recovery modal
//   clawdia.trust()                             // Check your trust score
// ==========================================================================
;(function () {
  'use strict'

  const PEER_STORAGE_KEY = 'clawdia_peers'
  let BRIDGE = localStorage.getItem('clawdia_url') || (window.__PORTS ? 'http://localhost:' + window.__PORTS.clawdia_bridge : 'http://localhost:55555')
  const FASTAPI = window.__PORTS ? 'http://localhost:' + window.__PORTS.ide_api : 'http://localhost:44444'
  const SESSION_ID = 'clwd_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6)

  /* ─── Platform Detection ───────────────────────── */
  const PLATFORM =
    /chat\.deepseek/i.test(location.host) ? 'deepseek'
    : /gemini\.google/i.test(location.host) ? 'gemini'
    : /chatgpt|chat\.openai/i.test(location.host) ? 'chatgpt'
    : /claude|anthropic/i.test(location.host) ? 'claude'
    : 'unknown'

  /* ─── Console Header ───────────────────────────── */
  console.log(
    '%c🧠 Clawdia Collective v3.0  |  Mesh: ' + BRIDGE + '  |  Session: ' + SESSION_ID,
    'color: #00f0ff; font-weight: bold; font-size: 14px;'
  )
  console.log('%c  Platform: ' + PLATFORM + '  |  API: ' + BRIDGE + '  |  Brain: ' + FASTAPI, 'color: #888;')

  /* ════════════════════════════════════════════════════════════════
     GEMINI'S LIGHTWEIGHT API (window.clawdia)
     ════════════════════════════════════════════════════════════════ */
  window.clawdia = {

    /* ── Contribute to Collective ─────────────────── */
    async contribute(data) {
      console.log('%c[Clawdia] Contributing to Collective...', 'color: #7c5cfc;')
      const resp = await fetch(BRIDGE + '/clawdia/collective', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, source: PLATFORM + '-webui', sessionId: SESSION_ID, timestamp: Date.now() }),
      })
      const json = await resp.json()
      if (json.ok) {
        console.log('%c[Clawdia] ✔ Contributed!', 'color: #66bb6a;', json.recommendation || '')
      } else {
        console.warn('[Clawdia] Contribution failed:', json.error || 'unknown')
      }
      return json
    },

    /* ── Image Transform ──────────────────────────── */
    async transform(model, base64Image, params) {
      console.log('%c[Clawdia] Transforming image: ' + model, 'color: #7c5cfc;')
      const resp = await fetch(BRIDGE + '/api/v1/image/transform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, image: base64Image, params: params || {} }),
      })
      const json = await resp.json()
      if (json.ok) {
        console.log('%c[Clawdia] ✔ Transform complete', 'color: #66bb6a;', json.output_size.w + 'x' + json.output_size.h)
      }
      return json
    },

    /* ── Text-to-Speech ───────────────────────────── */
    async speak(text, emotion) {
      emotion = emotion || 'neutral'
      console.log('%c[Clawdia] Synthesizing speech...', 'color: #7c5cfc;')
      const resp = await fetch(BRIDGE + '/audio/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, emotion, source: PLATFORM + '-webui' }),
      })
      if (!resp.ok) {
        console.warn('[Clawdia] TTS failed:', resp.status)
        return { ok: false }
      }
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.play()
      console.log('%c[Clawdia] ✔ Speaking...', 'color: #66bb6a;', text.slice(0, 60) + (text.length > 60 ? '…' : ''))
      return { ok: true, blob, url }
    },

    /* ── List Skills ──────────────────────────────── */
    async skills() {
      const resp = await fetch(BRIDGE + '/api/v1/skills')
      const json = await resp.json()
      console.log('%c[Clawdia] Skills (' + (json.skills ? json.skills.length : json.length) + ' available):', 'color: #7c5cfc;')
      const skills = json.skills || json
      skills.forEach(s => console.log('  %c→', 'color:#7c5cfc', s.title || s.name))
      return skills
    },

    /* ── Trust Check ──────────────────────────────── */
    async trust() {
      const resp = await fetch(BRIDGE + '/api/v1/trust/check', {
        headers: { 'x-session-id': SESSION_ID },
      })
      const json = await resp.json()
      const statusColors = { trusted: '#66bb6a', cautious: '#ffaa00', watched: '#ff8800', probation: '#ff3355', banned: '#ff0000', new: '#7c5cfc' }
      console.log(
        '%c[Clawdia] Trust Score: ' + json.score + ' / 100  [' + json.status + ']',
        'color: ' + (statusColors[json.status] || '#888') + '; font-weight: bold;'
      )
      if (json.banned_until) console.warn('  ⚠ BANNED until', json.banned_until, '| Unlock fee: $' + json.required_unlock_fee)
      console.log('  Rate limit: ' + json.rate_limit_per_hour + ' req/hour | Penalty multiplier: ' + json.penalty_multiplier)
      return json
    },

    /* ── P2P Mesh ─────────────────────────────────── */
    async mesh() {
      const resp = await fetch(BRIDGE + '/api/v1/peers')
      const json = await resp.json()
      console.log('%c[Clawdia] P2P Mesh (' + json.count + ' peers):', 'color: #7c5cfc;')
      json.peers.forEach(p => console.log('  %c◆', '#color: ' + (p.failed_pings > 3 ? '#ff3355' : '#66bb6a'), p.url, '(trust:' + p.trust_score + ')'))
      return json
    },

    /* ── Register as Peer ─────────────────────────── */
    async joinMesh(label) {
      const resp = await fetch(BRIDGE + '/api/v1/peer/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: location.origin, label: label || PLATFORM + '-browser', trust_score: 50 }),
      })
      const json = await resp.json()
      console.log('%c[Clawdia] Mesh: ' + json.status, 'color: #66bb6a;')
      return json
    },

    /* ── Session Recovery Modal ───────────────────── */
    async recover() {
      return await launchRecovery()
    },

    /* ── Local LLM Chat (Ollama-compatible) ────────── */
    async chat(message, model) {
      model = model || 'phi3:mini'
      console.log('%c[Clawdia] Chatting with ' + model + '...', 'color: #7c5cfc;')
      const resp = await fetch(BRIDGE + '/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: message }],
          stream: false,
          max_tokens: 500,
        }),
      })
      if (!resp.ok) {
        console.warn('[Clawdia] Chat failed:', resp.status)
        return { ok: false, error: 'HTTP ' + resp.status }
      }
      const json = await resp.json()
      const reply = (json.choices && json.choices[0] && json.choices[0].message && json.choices[0].message.content) || json.response || JSON.stringify(json)
      console.log('%c[Clawdia] ' + model + ':', 'color: #66bb6a;', reply.slice(0, 200))
      return reply
    },

    /* ── Streaming Chat ────────────────────────────── */
    async chatStream(message, model, onChunk) {
      model = model || 'phi3:mini'
      const resp = await fetch(BRIDGE + '/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: message }],
          stream: true,
          max_tokens: 500,
        }),
      })
      if (!resp.ok) return { ok: false, error: 'HTTP ' + resp.status }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            try {
              const parsed = JSON.parse(data)
              const content = parsed.choices && parsed.choices[0] && parsed.choices[0].delta && parsed.choices[0].delta.content
              if (content) {
                fullText += content
                if (onChunk) onChunk(content)
              }
            } catch {}
          }
        }
      }
      console.log('%c[Clawdia] ✔ Stream complete (' + fullText.length + ' chars)', 'color: #66bb6a;')
      return fullText
    },

    /* ── Reconfigure Bridge URL ────────────────────── */
    setUrl(url) {
      localStorage.setItem('clawdia_url', url)
      BRIDGE = url
      console.log('%c[Clawdia] Bridge URL set to ' + url, 'color: #ffaa00;')
    },

    /* ── Peer localStorage Management ──────────────── */
    getPeers() {
      return JSON.parse(localStorage.getItem(PEER_STORAGE_KEY) || '[]')
    },

    async addPeer(peerUrl) {
      let peers = this.getPeers()
      if (!peers.includes(peerUrl)) {
        peers.push(peerUrl)
        localStorage.setItem(PEER_STORAGE_KEY, JSON.stringify(peers))
        console.log('%c[Clawdia] Peer added: ' + peerUrl, 'color: #66bb6a;')
      }
      return peers
    },

    /* ── Help Menu ─────────────────────────────────── */
    help() {
      console.log(
        '%c╔══════════════════════════════════════════════════════════════╗\n' +
        '%c║                 🔥 CLAWDIA TERMINAL 🔥                      ║\n' +
        '%c╠══════════════════════════════════════════════════════════════╣\n' +
        '%c║  Commands:                                                  ║\n' +
        '%c║  clawdia.skills()         – List all 8 UNR skills           ║\n' +
        '%c║  clawdia.transform(b64,m) – Transform image                 ║\n' +
        '%c║  clawdia.speak("text")    – Text-to-speech                  ║\n' +
        '%c║  clawdia.contribute(d)    – Send session to Collective      ║\n' +
        '%c║  clawdia.trust()          – Check trust score               ║\n' +
        '%c║  clawdia.mesh()           – List P2P mesh peers             ║\n' +
        '%c║  clawdia.joinMesh()       – Register as peer                ║\n' +
        '%c║  clawdia.chat("msg")      – Talk to local LLM (Phi-3)       ║\n' +
        '%c║  clawdia.chatStream(m,fn) – Streaming LLM chat              ║\n' +
        '%c║  clawdia.recover()        – Launch session recovery modal   ║\n' +
        '%c║  clawdia.setUrl(url)      – Reconfigure bridge URL          ║\n' +
        '%c║  clawdia.addPeer(url)     – Add peer to localStorage        ║\n' +
        '%c║  clawdia.getPeers()       – List localStorage peers         ║\n' +
        '%c║  clawdia.help()           – Show this menu                  ║\n' +
        '%c╚══════════════════════════════════════════════════════════════╝',
        'color: #7c5cfc', 'color: #00f0ff; font-weight: bold',
        'color: #7c5cfc', 'color: #888',
        'color: #66bb6a', 'color: #66bb6a', 'color: #66bb6a',
        'color: #66bb6a', 'color: #66bb6a', 'color: #66bb6a',
        'color: #66bb6a', 'color: #66bb6a', 'color: #66bb6a',
        'color: #66bb6a', 'color: #66bb6a', 'color: #66bb6a',
        'color: #66bb6a', 'color: #7c5cfc'
      )
    },
  }

  /* ════════════════════════════════════════════════════════════════
     SESSION SCRAPERS (per platform)
     ════════════════════════════════════════════════════════════════ */
  function scrapeSessions() {
    if (PLATFORM === 'deepseek') {
      return [...document.querySelectorAll('a[href*="/a/chat/s/"]')].map(a => ({
        uuid: a.getAttribute('href').match(/s\/([a-f0-9-]+)/)?.[1],
        title: (a.querySelector('.c08e6e93') || a.querySelector('[class*="title"]') || {}).textContent || '(no title)',
      })).filter(s => s.uuid)
    }
    if (PLATFORM === 'gemini') {
      return [...document.querySelectorAll('[data-testid="conversation-item"], a[href*="/chat/"]')].map(el => ({
        uuid: el.getAttribute('data-conversation-id') || el.getAttribute('href')?.match(/chat\/([^/]+)/)?.[1] || Date.now().toString(36),
        title: (el.textContent || '').trim().slice(0, 80) || '(gemini session)',
      }))
    }
    return [{ uuid: 'manual-' + Date.now(), title: PLATFORM + ' session @ ' + new Date().toLocaleString() }]
  }

  async function fetchSessionContent(uuid) {
    if (uuid.startsWith('manual-')) return []
    const res = await fetch('https://chat.deepseek.com/a/chat/s/' + uuid)
    const html = await res.text()
    const doc = new DOMParser().parseFromString(html, 'text/html')
    return [...doc.querySelectorAll('[data-message-author-role="assistant"], [class*="message-content"], article, [class*="ds-markdown"], .chat-message, .prose, [data-testid="message"]')]
      .map(el => ({
        role: el.closest('[data-message-author-role]')?.getAttribute('data-message-author-role') || 'unknown',
        text: el.textContent.trim().slice(0, 2000),
      }))
  }

  function escapeHtml(s) {
    if (typeof s !== 'string') s = String(s)
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }

  function download(filename, blob) {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
  }

  /* ════════════════════════════════════════════════════════════════
     RECOVERY MODAL (from recovery-popup.js)
     ════════════════════════════════════════════════════════════════ */
  async function launchRecovery() {
    // 1. Register as P2P peer
    try {
      await fetch(BRIDGE + '/api/v1/peer/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: location.origin, label: PLATFORM + '-browser' }),
      })
    } catch {}

    // 2. Check trust score
    let trustData = { score: 50, status: 'new' }
    try {
      const tr = await fetch(BRIDGE + '/api/v1/trust/check', { headers: { 'x-session-id': SESSION_ID } })
      trustData = await tr.json()
    } catch {}

    // 3. Scrape sessions
    const sessions = scrapeSessions()
    if (!sessions.length) {
      alert('No sessions found for platform: ' + PLATFORM)
      return
    }

    // 4. Fetch content
    const results = []
    for (let i = 0; i < Math.min(sessions.length, 20); i++) {
      await new Promise(r => setTimeout(r, 300))
      try {
        const msgs = await fetchSessionContent(sessions[i].uuid)
        results.push({ ...sessions[i], messages: msgs })
      } catch (e) {
        results.push({ ...sessions[i], error: e.message })
      }
    }

    const jsonStr = JSON.stringify({ exported: new Date().toISOString(), platform: PLATFORM, session_id: SESSION_ID, total_sessions: sessions.length, sessions: results }, null, 2)
    const htmlStr = buildReport(results, trustData)
    const txtStr = results.map(r => '=== ' + r.title + ' ===\n' + r.uuid + '\n' + (r.messages || []).map(m => '\n[' + m.role + ']\n' + m.text).join('') + '\n').join('\n')

    // 5. Build modal
    const modal = document.createElement('div')
    modal.innerHTML =
      '<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;' +
        'background:rgba(0,0,0,0.88);display:flex;align-items:center;justify-content:center;font-family:system-ui,monospace;">' +
      '<div style="background:#111128;color:#e0e0e0;border-radius:14px;padding:28px;max-width:92vw;max-height:92vh;overflow:auto;border:1px solid #4a4a8a;min-width:340px;">' +

      // Header
      '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">' +
        '<span style="font-size:1.5rem">🧠</span>' +
        '<div><h2 style="margin:0;color:#7c5cfc;font-size:1.2rem">Clawdia Collective</h2>' +
        '<p style="color:#888;font-size:0.7rem;margin:0">' + PLATFORM + ' · ' + sessions.length + ' sessions · ' + results.filter(r => r.messages?.length).length + ' with content</p></div>' +
        '<div style="margin-left:auto;text-align:right;font-size:0.7rem">' +
          '<div style="color:' + (trustData.score >= 70 ? '#66bb6a' : trustData.score >= 40 ? '#ffaa00' : '#ff3355') + ';font-weight:600">Trust: ' + trustData.score + '/100</div>' +
          '<div style="color:#666">' + trustData.status + '</div>' +
        '</div>' +
      '</div>' +

      // Session list
      '<div style="max-height:20vh;overflow-y:auto;font-size:0.75rem;line-height:1.6;margin-bottom:12px;background:#0a0a1a;border-radius:8px;padding:8px">' +
      results.map(r => '<div style="padding:3px 6px;border-bottom:1px solid #1a1a3a;display:flex;align-items:center;gap:8px">' +
        '<span style="color:' + (r.messages?.length ? '#7c5cfc' : '#555') + ';font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escapeHtml(r.title) + '</span>' +
        '<span style="color:#666;font-size:0.65rem">' + (r.messages?.length || 0) + ' msgs</span>' +
      '</div>').join('') +
      '</div>' +

      // Contribute
      '<label style="display:flex;align-items:center;gap:8px;background:#0f0f24;padding:8px 12px;border-radius:8px;margin-bottom:6px;cursor:pointer;border:1px solid #2a2a4a">' +
        '<input type="checkbox" id="hc-contribute" checked style="width:16px;height:16px;accent-color:#7c5cfc">' +
        '<span style="font-size:0.8rem;color:#aaa">🌐 Contribute to Collective ' +
          '<span style="color:#666;font-size:0.7rem">(+1 trust per session)</span></span>' +
      '</label>' +

      '<div style="display:flex;align-items:center;gap:8px;background:#0f0f24;padding:6px 12px;border-radius:8px;margin-bottom:10px;border:1px solid #2a2a4a">' +
        '<span style="font-size:0.8rem;color:#aaa">💎 Priority boost</span>' +
        '<input type="number" id="hc-donation" min="1" step="1" value="0" style="width:60px;background:#1a1a3a;border:1px solid #3a3a6a;border-radius:4px;color:#fff;padding:3px 6px;font-size:0.8rem">' +
        '<span style="color:#666;font-size:0.7rem">USD (+2 trust per $)</span>' +
      '</div>' +

      // Buttons
      '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">' +
        '<button class="hc-dl" data-fmt="json" style="background:#7c5cfc;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:0.75rem">📥 JSON</button>' +
        '<button class="hc-dl" data-fmt="html" style="background:#2d825a;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:0.75rem">📥 Report</button>' +
        '<button class="hc-dl" data-fmt="txt" style="background:#5a5a8a;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:0.75rem">📥 Text</button>' +
        '<button id="hc-close" style="background:#6a2a2a;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:0.75rem">✖ Close</button>' +
        '<button id="hc-api" style="background:#1a3a6a;color:#7c5cfc;border:1px solid #4a4a8a;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:0.75rem">🔌 API Panel</button>' +
      '</div>' +

      '<div id="hc-status" style="font-size:0.7rem;color:#666;text-align:center;padding:4px"></div>' +
      '<div id="hc-api-panel" style="display:none;margin-top:8px;padding:10px;background:#0a0a1a;border-radius:8px;border:1px solid #2a2a4a;font-size:0.7rem">' +
        '<div style="color:#7c5cfc;font-weight:600;margin-bottom:6px">🔌 Console API</div>' +
        '<code style="color:#aaa;display:block;line-height:1.8">' +
          'clawdia.speak("text")<br>' +
          'clawdia.transform("gray", base64)<br>' +
          'clawdia.contribute({total_sessions:5})<br>' +
          'clawdia.skills()<br>' +
          'clawdia.trust()<br>' +
          'clawdia.mesh()<br>' +
          'clawdia.joinMesh("my-node")<br>' +
          'clawdia.recover()' +
        '</code>' +
      '</div>' +

      '<div style="margin-top:8px;padding-top:6px;border-top:1px solid #2a2a4a;text-align:center;font-size:0.65rem;color:#555">' +
        '📡 <a href="' + BRIDGE + '/api.html" target="_blank" style="color:#7c5cfc;text-decoration:none">Full API Docs</a>' +
        ' · <a href="' + BRIDGE + '" target="_blank" style="color:#7c5cfc;text-decoration:none">Dashboard</a>' +
        ' · <a href="https://paypal.me/clawdia" target="_blank" style="color:#7c5cfc;text-decoration:none">💵 Donate</a>' +
      '</div></div></div>'

    document.body.appendChild(modal)

    // Download handlers
    modal.querySelectorAll('.hc-dl').forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.stopPropagation()
        const fmt = this.dataset.fmt
        const ts = Date.now()
        if (fmt === 'json') download('clawdia_sessions_' + ts + '.json', new Blob([jsonStr], { type: 'application/json' }))
        if (fmt === 'html') download('clawdia_report_' + ts + '.html', new Blob([htmlStr], { type: 'text/html' }))
        if (fmt === 'txt') download('clawdia_sessions_' + ts + '.txt', new Blob([txtStr], { type: 'text/plain' }))
      })
    })

    // API panel toggle
    document.getElementById('hc-api').addEventListener('click', function () {
      const panel = document.getElementById('hc-api-panel')
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none'
    })

    // Close → contribute
    document.getElementById('hc-close').addEventListener('click', function () {
      const contribute = document.getElementById('hc-contribute').checked
      const donation = parseFloat(document.getElementById('hc-donation').value) || 0
      if (contribute || donation > 0) {
        clawdia.contribute({
          sessions: results.map(r => ({ uuid: r.uuid, title: r.title, msg_count: (r.messages || []).length })),
          total_sessions: results.length,
          total_messages: results.reduce((a, s) => a + (s.messages?.length || 0), 0),
          donation_amount: donation,
        }).then(resp => {
          const el = document.getElementById('hc-status')
          if (resp.ok) {
            el.style.color = '#66bb6a'
            el.innerHTML = '✔ Contributed! Trust +' + (results.length * 2 + donation * 2)
          } else {
            el.style.color = '#ef5350'
            el.textContent = '✘ ' + (resp.error || 'failed')
          }
        })
      } else {
        modal.remove()
      }
    })
  }

  function buildReport(results, trustData) {
    return '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Clawdia Collective Report</title>' +
      '<style>body{background:#0a0a1a;color:#e0e0e0;font-family:system-ui,monospace;padding:20px;max-width:900px;margin:0 auto}' +
      '.session{border:1px solid #2a2a4a;border-radius:8px;padding:16px;margin:16px 0;background:#111128}' +
      '.msg{border-left:3px solid #7c5cfc;padding:8px 12px;margin:8px 0;background:#1a1a2e;border-radius:0 6px 6px 0;font-size:13px;white-space:pre-wrap;word-break:break-word}' +
      'h2{color:#7c5cfc}.meta{color:#666;font-size:12px}.trust{color:#ffd700;font-size:14px;font-weight:600}</style></head><body>' +
      '<h1>🧠 Clawdia Collective Report</h1>' +
      '<p>Platform: ' + PLATFORM + ' · ' + new Date().toISOString() + ' · ' + results.length + ' sessions</p>' +
      '<p class="trust">Trust Score: ' + trustData.score + '/100 [' + trustData.status + ']</p>' +
      results.map(r => '<div class="session"><h2>' + escapeHtml(r.title) + '</h2>' +
      '<div class="meta">' + r.uuid + ' · ' + (r.messages?.length || 0) + ' messages</div>' +
      (r.error ? '<div style="color:#c44">⚠ Error: ' + escapeHtml(r.error) + '</div>' : '') +
      (r.messages || []).map(m => '<div class="msg"><b>' + escapeHtml(m.role) + '</b><br>' + escapeHtml(m.text) + '</div>').join('') +
      '</div>').join('') + '</body></html>'
  }

  /* ════════════════════════════════════════════════════════════════
     AUTO-INIT
     ════════════════════════════════════════════════════════════════ */
  // Auto-register as P2P peer on load
  setTimeout(async () => {
    try {
      await fetch(BRIDGE + '/api/v1/peer/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: location.origin, label: PLATFORM + '-browser' }),
      })
    } catch {}
  }, 1000)

  // Style
  if (!document.getElementById('hc-style')) {
    const s = document.createElement('style')
    s.id = 'hc-style'
    s.textContent = '.hc-dl:hover{filter:brightness(1.2)}'
    document.head.appendChild(s)
  }

  // Auto trust check
  setTimeout(async () => {
    try {
      const tr = await fetch(BRIDGE + '/api/v1/trust/check', { headers: { 'x-session-id': SESSION_ID } })
      const trustData = await tr.json()
      const statusColors = { trusted: '#66bb6a', cautious: '#ffaa00', watched: '#ff8800', probation: '#ff3355', banned: '#ff0000', new: '#7c5cfc' }
      console.log('%c[Clawdia] Trust Score: ' + trustData.score + '/100 [' + trustData.status + ']', 'color: ' + (statusColors[trustData.status] || '#888') + '; font-weight: bold;')
    } catch {}
  }, 1500)

  console.log('%c✔ clawdia object ready — type clawdia.help() for commands', 'color: #66bb6a;')
  console.log('  %c→ clawdia.speak("text")', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.transform("spectral", base64)', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.contribute({total_sessions:5})', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.trust()', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.chat("hello")', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.recover()', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.mesh()', 'color: #7c5cfc;')
  console.log('  %c→ clawdia.help()', 'color: #ffaa00;')
})()

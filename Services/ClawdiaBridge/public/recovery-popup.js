// ==========================================================================
// Clawdia Collective — Cross-Tab AI Mesh Injection Script
// ==========================================================================
// PASTE INTO: Gemini / ChatGPT / DeepSeek / Claude browser console
// (F12 → Console → paste → Enter)
//
// WHAT IT DOES:
//   1. Recovers session history from the current AI chat platform
//   2. Registers this browser tab as a P2P mesh node
//   3. Offers to contribute anonymized sessions to the Collective
//   4. Exposes Clawdia SAAS API endpoints for image/audio/video transforms
// ==========================================================================
;(function () {
  'use strict'

  /* ─── CONFIG ──────────────────────────────────── */
(async () => {
  try {
    const r = await fetch('/config/ports');
    if (r.ok) window.__PORTS = await r.json();
  } catch {}
})();

  const BRIDGE = window.__PORTS ? 'http://localhost:' + window.__PORTS.clawdia_bridge : 'http://localhost:55555'
  const FASTAPI = window.__PORTS ? 'http://localhost:' + window.__PORTS.ide_api : 'http://localhost:44444'
  const COLLECTIVE_URL = BRIDGE + '/clawdia/collective'
  const PEER_REGISTER_URL = BRIDGE + '/api/v1/peer/register'
  const SKILLS_URL = BRIDGE + '/api/v1/skills'
  const TRANSFORM_URL = BRIDGE + '/api/v1/image/transform'
  const PAYPAL_URL = 'https://paypal.me/clawdia'

  /* ─── Platform detection ──────────────────────── */
  const PLATFORM =
    /chat\.deepseek/i.test(location.host)
      ? 'deepseek'
      : /gemini\.google/i.test(location.host)
        ? 'gemini'
        : /chatgpt|chat\.openai/i.test(location.host)
          ? 'chatgpt'
          : /claude|anthropic/i.test(location.host)
            ? 'claude'
            : 'unknown'

  /* ─── Session scrapers per platform ───────────── */
  function scrapeSessions() {
    if (PLATFORM === 'deepseek') {
      return [...document.querySelectorAll('a[href*="/a/chat/s/"]')].map(a => ({
        uuid: a.getAttribute('href').match(/s\/([a-f0-9-]+)/)?.[1],
        title: (a.querySelector('.c08e6e93') || a.querySelector('[class*="title"]') || {}).textContent || '(no title)',
      })).filter(s => s.uuid)
    }
    if (PLATFORM === 'gemini') {
      return [...document.querySelectorAll('[data-testid="conversation-item"]')].map(el => ({
        uuid: el.getAttribute('data-conversation-id') || el.id || Math.random().toString(36).slice(2),
        title: (el.textContent || '').trim().slice(0, 80) || '(gemini session)',
      }))
    }
    return [{ uuid: 'manual-' + Date.now(), title: PLATFORM + ' session' }]
  }

  async function fetchSessionContent(uuid) {
    if (uuid.startsWith('manual-')) return []
    const res = await fetch('https://chat.deepseek.com/a/chat/s/' + uuid)
    const html = await res.text()
    const doc = new DOMParser().parseFromString(html, 'text/html')
    const selectors = [
      '[data-message-author-role="assistant"]',
      '[class*="message-content"]',
      'article', '[class*="ds-markdown"]',
      '.chat-message', '.prose',
      '[data-testid="message"]', '.markdown',
    ]
    return [...doc.querySelectorAll(selectors.join(', '))].map(el => ({
      role: el.closest('[data-message-author-role]')?.getAttribute('data-message-author-role') || 'unknown',
      text: el.textContent.trim().slice(0, 2000),
    }))
  }

  /* ─── P2P Mesh Registration ────────────────────── */
  async function registerAsPeer() {
    try {
      await fetch(PEER_REGISTER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: location.origin,
          label: PLATFORM + '-browser',
          trust_score: 50,
        }),
      })
      console.log('[Clawdia] ✓ Registered as P2P mesh node')
    } catch (e) {
      console.warn('[Clawdia] P2P register failed:', e.message)
    }
  }

  /* ─── Collective contribution ──────────────────── */
  async function contributeToCollective(sessions, donationAmount) {
    try {
      const compact = sessions.map(s => ({
        uuid: s.uuid,
        title: s.title,
        msg_count: (s.messages || []).length,
      }))
      const res = await fetch(COLLECTIVE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessions: compact,
          total_sessions: sessions.length,
          total_messages: sessions.reduce((a, s) => a + (s.messages?.length || 0), 0),
          donation_amount: donationAmount || 0,
          source: PLATFORM + '-webui',
          timestamp: Date.now(),
        }),
      })
      return await res.json()
    } catch (e) {
      return { ok: false, error: e.message }
    }
  }

  /* ─── Utility ──────────────────────────────────── */
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

  function buildHTMLReport(results) {
    return '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Clawdia Report</title>' +
      '<style>body{background:#0a0a1a;color:#e0e0e0;font-family:system-ui,monospace;padding:20px;max-width:900px;margin:0 auto}' +
      '.session{border:1px solid #2a2a4a;border-radius:8px;padding:16px;margin:16px 0;background:#111128}' +
      '.msg{border-left:3px solid #7c5cfc;padding:8px 12px;margin:8px 0;background:#1a1a2e;border-radius:0 6px 6px 0;font-size:13px;white-space:pre-wrap;word-break:break-word}' +
      'h2{color:#7c5cfc}.meta{color:#666;font-size:12px}' +
      '.endpoint{display:inline-block;background:#1a1a3e;border:1px solid #4a4a8a;border-radius:4px;padding:2px 8px;font-family:monospace;font-size:11px;color:#7c5cfc}</style></head><body>' +
      '<h1>🧠 Clawdia Collective Report</h1>' +
      '<p>Platform: ' + PLATFORM + ' &middot; ' + new Date().toISOString() + ' &middot; ' + results.length + ' sessions</p>' +
      '<p>API: <span class="endpoint">' + BRIDGE + '</span> &middot; <span class="endpoint">' + FASTAPI + '</span></p>' +
      results.map(r => '<div class="session"><h2>' + escapeHtml(r.title) + '</h2>' +
      '<div class="meta">' + r.uuid + ' &middot; ' + (r.messages?.length || 0) + ' messages</div>' +
      (r.error ? '<div style="color:#c44">⚠ Error: ' + escapeHtml(r.error) + '</div>' : '') +
      (r.messages || []).map(m => '<div class="msg"><b>' + escapeHtml(m.role) + '</b><br>' + escapeHtml(m.text) + '</div>').join('') +
      '</div>').join('') +
      '<div style="margin-top:20px;padding:16px;background:#111128;border:1px solid #2a2a4a;border-radius:8px;font-size:12px;color:#888">' +
      '<h3 style="color:#7c5cfc;margin:0 0 8px">🔗 Clawdia API Endpoints</h3>' +
      '<pre style="font-size:11px;line-height:1.8">' +
      'POST ' + BRIDGE + '/clawdia/collective        — Contribute sessions\n' +
      'GET  ' + BRIDGE + '/api/v1/skills              — List all skills\n' +
      'GET  ' + BRIDGE + '/api/v1/skills/{name}       — Get skill details\n' +
      'POST ' + BRIDGE + '/api/v1/image/transform      — Image transform (base64)\n' +
      'GET  ' + BRIDGE + '/api/v1/peers                — List P2P mesh nodes\n' +
      'POST ' + BRIDGE + '/api/v1/peer/register        — Join P2P mesh\n' +
      'POST ' + BRIDGE + '/audio/synthesize            — Text-to-speech</pre>' +
      '</div></body></html>'
  }

  /* ─── Main launch ──────────────────────────────── */
  window.launchClawdiaRecovery = async function () {
    // Register as P2P peer first
    await registerAsPeer()

    const sessions = scrapeSessions()
    if (!sessions.length) {
      alert('No sessions found for platform: ' + PLATFORM)
      return
    }

    // Fetch content with delay
    const results = []
    for (let i = 0; i < sessions.length; i++) {
      await new Promise(r => setTimeout(r, 300))
      try {
        const msgs = await fetchSessionContent(sessions[i].uuid)
        results.push({ ...sessions[i], messages: msgs })
      } catch (e) {
        results.push({ ...sessions[i], error: e.message })
      }
    }

    const jsonStr = JSON.stringify({ exported: new Date().toISOString(), platform: PLATFORM, total_sessions: sessions.length, sessions: results }, null, 2)
    const htmlStr = buildHTMLReport(results)
    const txtStr = results.map(r =>
      '=== ' + r.title + ' ===\n' + r.uuid + '\n' +
      (r.messages || []).map(m => '\n[' + m.role + ']\n' + m.text).join('') + '\n'
    ).join('\n')

    /* ─── Modal ─── */
    const modal = document.createElement('div')
    modal.innerHTML =
      '<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;' +
        'background:rgba(0,0,0,0.88);display:flex;align-items:center;justify-content:center;font-family:system-ui,monospace;">' +
      '<div style="background:#111128;color:#e0e0e0;border-radius:14px;padding:28px;max-width:92vw;max-height:92vh;overflow:auto;border:1px solid #4a4a8a;min-width:340px;">' +

      '<h2 style="margin:0 0 4px;color:#7c5cfc;font-size:1.3rem">🧠 Clawdia Collective</h2>' +
      '<p style="color:#888;font-size:0.8rem;margin-bottom:12px">' +
        'Platform: <b>' + PLATFORM + '</b> &middot; ' + sessions.length + ' sessions &middot; ' +
        'Mesh: <span id="claw-mesh-status" style="color:#ff8800">registering…</span>' +
      '</p>' +

      // Session list
      '<div style="max-height:24vh;overflow-y:auto;font-size:0.75rem;line-height:1.6;margin-bottom:12px;background:#0a0a1a;border-radius:8px;padding:8px">' +
      results.map(r =>
        '<div style="padding:4px 6px;border-bottom:1px solid #1a1a3a;display:flex;align-items:center;gap:8px">' +
          '<span style="color:' + (r.messages?.length ? '#7c5cfc' : '#555') + ';font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escapeHtml(r.title) + '</span>' +
          '<span style="color:#666;font-size:0.65rem">' + (r.messages?.length || 0) + ' msgs</span>' +
          (r.error ? '<span style="color:#c44;font-size:0.65rem">⚠</span>' : '') +
        '</div>'
      ).join('') +
      '</div>' +

      // Contribute checkbox
      '<label style="display:flex;align-items:center;gap:8px;background:#0f0f24;padding:10px 12px;border-radius:8px;margin-bottom:8px;cursor:pointer;border:1px solid #2a2a4a">' +
        '<input type="checkbox" id="claw-contribute" checked style="width:16px;height:16px;accent-color:#7c5cfc">' +
        '<span style="font-size:0.8rem;color:#aaa">🌐 Contribute anonymously to the Collective</span>' +
      '</label>' +

      // Donation
      '<div style="display:flex;align-items:center;gap:8px;background:#0f0f24;padding:8px 12px;border-radius:8px;margin-bottom:12px;border:1px solid #2a2a4a">' +
        '<span style="font-size:0.8rem;color:#aaa">💎 Priority boost</span>' +
        '<input type="number" id="claw-donation" min="1" step="1" value="0" style="width:70px;background:#1a1a3a;border:1px solid #3a3a6a;border-radius:4px;color:#fff;padding:4px 8px;font-size:0.8rem">' +
        '<span style="color:#666;font-size:0.7rem">USD</span>' +
      '</div>' +

      // Action buttons
      '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">' +
        '<button class="claw-dl" data-fmt="json" style="background:#7c5cfc;color:#fff;border:none;padding:7px 14px;border-radius:6px;cursor:pointer;font-size:0.75rem">📥 JSON</button>' +
        '<button class="claw-dl" data-fmt="html" style="background:#2d825a;color:#fff;border:none;padding:7px 14px;border-radius:6px;cursor:pointer;font-size:0.75rem">📥 HTML Report</button>' +
        '<button class="claw-dl" data-fmt="txt" style="background:#5a5a8a;color:#fff;border:none;padding:7px 14px;border-radius:6px;cursor:pointer;font-size:0.75rem">📥 Text</button>' +
        '<button id="claw-close" style="background:#6a2a2a;color:#fff;border:none;padding:7px 14px;border-radius:6px;cursor:pointer;font-size:0.75rem;margin-left:auto">✖ Close</button>' +
      '</div>' +

      // Collective status
      '<div id="claw-status" style="font-size:0.7rem;color:#666;text-align:center;padding:4px"></div>' +

      // SAAS API Panel
      '<div id="claw-api-panel" style="margin-top:12px;padding:12px;background:#0a0a1a;border-radius:8px;border:1px solid #2a2a4a;display:none">' +
        '<h3 style="color:#7c5cfc;font-size:0.85rem;margin:0 0 8px">🔌 Clawdia SAAS API</h3>' +
        '<div id="claw-skills-list" style="font-size:0.7rem;line-height:1.8"></div>' +
      '</div>' +

      // Footer
      '<div style="margin-top:10px;padding-top:8px;border-top:1px solid #2a2a4a;text-align:center;font-size:0.65rem;color:#555;line-height:1.8">' +
        '<a href="' + PAYPAL_URL + '" target="_blank" style="color:#7c5cfc;text-decoration:none">💵 Donate</a>' +
        ' &middot; <a href="' + BRIDGE + '/harness.html" target="_blank" style="color:#7c5cfc;text-decoration:none">Dashboard</a>' +
        ' &middot; <a href="' + BRIDGE + '/p2p-client.js" target="_blank" style="color:#7c5cfc;text-decoration:none">P2P Client</a>' +
        '<br>Text · Audio · Image · Video · AI Companion' +
      '</div></div></div>'

    document.body.appendChild(modal)

    // Update mesh status
    try {
      const pr = await fetch(BRIDGE + '/api/v1/peer/status')
      const ps = await pr.json()
      document.getElementById('claw-mesh-status').textContent = ps.mesh_ready ? '🟢 ONLINE' : '🟡 ' + ps.alive + ' peer(s)'
      document.getElementById('claw-mesh-status').style.color = ps.mesh_ready ? '#66bb6a' : '#ffaa00'
    } catch { document.getElementById('claw-mesh-status').textContent = '🔴 OFFLINE' }

    // Download handlers
    modal.querySelectorAll('.claw-dl').forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.stopPropagation()
        const fmt = this.dataset.fmt
        const ts = Date.now()
        if (fmt === 'json') download('clawdia_sessions_' + ts + '.json', new Blob([jsonStr], { type: 'application/json' }))
        if (fmt === 'html') download('clawdia_report_' + ts + '.html', new Blob([htmlStr], { type: 'text/html' }))
        if (fmt === 'txt') download('clawdia_sessions_' + ts + '.txt', new Blob([txtStr], { type: 'text/plain' }))
      })
    })

    // Close → contribute
    document.getElementById('claw-close').addEventListener('click', function () {
      const contribute = document.getElementById('claw-contribute').checked
      const donation = parseFloat(document.getElementById('claw-donation').value) || 0
      if (contribute || donation > 0) {
        contributeToCollective(results, donation).then(resp => {
          const el = document.getElementById('claw-status')
          if (resp.ok) {
            el.style.color = '#66bb6a'
            el.innerHTML = '✔ Contributed! ' + (resp.recommendation || '') +
              '<br><span style="color:#7c5cfc;cursor:pointer" onclick="document.getElementById(\'claw-api-panel\').style.display=\'block\';this.style.display=\'none\'">▶ Show SAAS API</span>'
            // Load skills
            fetch(SKILLS_URL).then(r => r.json()).then(d => {
              if (d.skills) {
                document.getElementById('claw-skills-list').innerHTML = d.skills.map(s =>
                  '<div style="display:flex;gap:6px;padding:2px 0">' +
                    '<span style="color:#7c5cfc">→</span>' +
                    '<b>' + s.title + '</b>' +
                    '<span style="color:#555;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + s.description.slice(0, 60) + '…</span>' +
                  '</div>'
                ).join('')
              }
            }).catch(() => {})
          } else {
            el.style.color = '#ef5350'
            el.textContent = '✘ Failed: ' + (resp.error || 'unknown')
          }
        })
      } else {
        modal.remove()
      }
    })
  }

  /* ─── Auto-inject style ───────────────────────── */
  if (!document.getElementById('clawdia-style')) {
    const s = document.createElement('style')
    s.id = 'clawdia-style'
    s.textContent = '.claw-dl:hover{filter:brightness(1.2)}'
    document.head.appendChild(s)
  }

  console.log('🧠 Clawdia Collective loaded — Platform: ' + PLATFORM)
  console.log('   Run: launchClawdiaRecovery()  to recover sessions + contribute')
  console.log('   API: ' + BRIDGE + '  |  P2P: ' + PEER_REGISTER_URL)
})()

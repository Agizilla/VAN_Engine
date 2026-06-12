// ==========================================================================
// DeepSeek → VAN_Engine Comms Test + DOM Buttons (RESEND LAST / SPEAK LAST)
// ==========================================================================
// Paste into DeepSeek browser console.
// Adds RESEND LAST and SPEAK LAST buttons to the toolbar after testing.
// ==========================================================================
(async function deepseekCommsTestV3() {
  // Try to fetch port config; fallback if CORS blocks it
  let BRIDGE_PORT = 55555;
  try { const r = await fetch('http://localhost:55555/config/ports', { mode: 'cors' }); if (r.ok) { const p = await r.json(); BRIDGE_PORT = p.clawdia_bridge; } } catch {}
  const BRIDGE = `http://127.0.0.1:${BRIDGE_PORT}`
  const SESSION_ID = 'ds_test_' + Date.now() + '_' + Math.random().toString(36).slice(2,8)
  
  console.log('%c╔══════════════════════════════════════════════════════╗', 'color:#00f0ff')
  console.log('%c║   🦞 DEEPSEEK → CLAWDIA BRIDGE COMMS TEST            ║', 'color:#00f0ff;font-weight:bold')
  console.log('%c║   Session: ' + SESSION_ID, 'color:#888')
  console.log('%c╚══════════════════════════════════════════════════════╝', 'color:#00f0ff')
  
  const results = []
  
  async function test(name, url, options = {}) {
    try {
      const res = await fetch(url, { ...options, mode: 'cors' })
      const data = res.ok ? await res.text().then(t => t.slice(0, 80)) : 'HTTP ' + res.status
      console.log(`✅ ${name}:`, res.status, data)
      results.push({ name, ok: true })
      return true
    } catch(e) {
      console.log(`❌ ${name}:`, e.message)
      results.push({ name, ok: false })
      return false
    }
  }
  
  await test('Bridge Root', `${BRIDGE}/`)
  
  try {
    const trust = await fetch(`${BRIDGE}/api/v1/trust/check`, {
      headers: { 'x-session-id': SESSION_ID }
    })
    const trustData = await trust.json()
    console.log(`✅ Trust Check:`, trust.status, trustData)
    results.push({ name: 'Trust Check', ok: true })
  } catch(e) {
    console.log(`❌ Trust Check:`, e.message)
    results.push({ name: 'Trust Check', ok: false })
  }
  
  await test('Trust Ledger', `${BRIDGE}/api/v1/trust/ledger?limit=3`)
  await test('Peers List', `${BRIDGE}/api/v1/peers`)
  await test('Peer Status', `${BRIDGE}/api/v1/peer/status`)
  await test('Skills', `${BRIDGE}/api/v1/skills`)
  await test('Inbox', `${BRIDGE}/clawdia/inbox`)
  
  try {
    const msg = await fetch(`${BRIDGE}/clawdia`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        source: 'deepseek-webui', 
        text: `Hello from DeepSeek! Session: ${SESSION_ID}` 
      })
    })
    const msgData = await msg.json()
    console.log(`✅ Send Message:`, msg.status, msgData)
    results.push({ name: 'Send Message', ok: true })
  } catch(e) {
    console.log(`❌ Send Message:`, e.message)
    results.push({ name: 'Send Message', ok: false })
  }
  
  const passed = results.filter(r => r.ok).length
  console.log('\n%c╔══════════════════════════════════════════════════════╗', 'color:#00f0ff')
  console.log(`%c║  RESULTS: ${passed}/${results.length} PASSED`, 'color:#00f0ff;font-weight:bold')
  console.log('%c╚══════════════════════════════════════════════════════╝', 'color:#00f0ff')
  
  window.clawdiaBridge = {
    trust: () => fetch(`${BRIDGE}/api/v1/trust/check`, { headers: { 'x-session-id': Date.now() } }).then(r => r.json()),
    peers: () => fetch(`${BRIDGE}/api/v1/peers`).then(r => r.json()),
    skills: () => fetch(`${BRIDGE}/api/v1/skills`).then(r => r.json()),
    inbox: () => fetch(`${BRIDGE}/clawdia/inbox`).then(r => r.json()),
    send: (text) => fetch(`${BRIDGE}/clawdia`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: 'console', text }) }).then(r => r.json()),
    speak: (text) => fetch(`${BRIDGE}/audio/synthesize`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: 'deepseek-webui', text, emotion: 'neutral', intensity: 1.0 }) }).then(r => r.json()),
    results: results
  }

  // ── Inject RESEND LAST + SPEAK LAST buttons into DeepSeek toolbar ──
  function injectButtons() {
    const container = document.querySelector('._58b31c9')
    if (!container) {
      console.log('%c⚠ Could not find toolbar container (_58b31c9) — buttons not injected', 'color:#d29922')
      return
    }

    const style = document.createElement('style')
    style.textContent = `
      .cd-btn {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600;
        border: 1px solid rgba(255,255,255,0.15); cursor: pointer;
        transition: all 0.15s; background: rgba(255,255,255,0.06); color: #c9d1d9;
        margin-left: 6px; height: 28px;
      }
      .cd-btn:hover { background: rgba(88,166,255,0.2); border-color: #58a6ff; color: #58a6ff; }
      .cd-btn:active { transform: scale(0.96); }
      .cd-btn.speak { border-color: rgba(63,185,80,0.3); }
      .cd-btn.speak:hover { background: rgba(63,185,80,0.2); border-color: #3fb950; color: #3fb950; }
      .cd-btn-spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid rgba(255,255,255,0.15); border-top-color: #58a6ff; border-radius: 50%; animation: cd-spin 0.6s linear infinite; }
      @keyframes cd-spin { to { transform: rotate(360deg); } }
    `
    document.head.appendChild(style)

    const resendBtn = document.createElement('button')
    resendBtn.className = 'cd-btn'
    resendBtn.innerHTML = '↻ RESEND LAST'
    resendBtn.title = 'Resend last message to ClawdiaBridge'

    const speakBtn = document.createElement('button')
    speakBtn.className = 'cd-btn speak'
    speakBtn.innerHTML = '🔊 SPEAK LAST'
    speakBtn.title = 'Send last message to voice server for TTS'

    container.appendChild(resendBtn)
    container.appendChild(speakBtn)

    async function getLastMessage() {
      try {
        const res = await fetch(`${BRIDGE}/clawdia/inbox`)
        const data = await res.json()
        const items = data.value || data
        const arr = Array.isArray(items) ? items : []
        return arr.length > 0 ? arr[arr.length - 1] : null
      } catch { return null }
    }

    resendBtn.onclick = async () => {
      const msg = await getLastMessage()
      if (!msg) { console.log('%c❌ No messages in inbox to resend', 'color:#f85149'); return }
      resendBtn.innerHTML = '<span class="cd-btn-spinner"></span>'
      try {
        const res = await fetch(`${BRIDGE}/clawdia`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: msg.source || 'deepseek-webui', text: msg.text })
        })
        const d = await res.json()
        console.log(`%c↻ Resent: "${msg.text.slice(0, 60)}..." → id=${d.id}`, 'color:#58a6ff')
      } catch(e) { console.log('%c❌ Resend failed:', 'color:#f85149', e.message) }
      resendBtn.innerHTML = '↻ RESEND LAST'
    }

    speakBtn.onclick = async () => {
      const msg = await getLastMessage()
      if (!msg) { console.log('%c❌ No messages in inbox to speak', 'color:#f85149'); return }
      speakBtn.innerHTML = '<span class="cd-btn-spinner"></span>'
      try {
        const res = await fetch(`${BRIDGE}/audio/synthesize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: 'deepseek-webui', text: msg.text, emotion: 'neutral', intensity: 1.0 })
        })
        const d = await res.json()
        console.log(`%c🔊 Sent to voice server: "${msg.text.slice(0, 60)}..." → ${d.ok ? 'OK' : 'FAIL'}`, d.ok ? 'color:#3fb950' : 'color:#f85149', d)
      } catch(e) { console.log('%c❌ Speak failed:', 'color:#f85149', e.message) }
      speakBtn.innerHTML = '🔊 SPEAK LAST'
    }

    console.log('%c↻ RESEND LAST · 🔊 SPEAK LAST — buttons injected into toolbar', 'color:#3fb950')
  }

  // Wait a tick for DOM to settle, then inject
  setTimeout(injectButtons, 500)

  console.log('\n🔧 Try: await clawdiaBridge.peers()')
  console.log('🔧 Try: await clawdiaBridge.send("Hello from console!")')
  console.log('🔧 Try: await clawdiaBridge.speak("Hello, this is DeepSeek speaking!")')
  
  return results
})()

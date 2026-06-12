/* ==========================================================================
 * P2P Collective Client — Phase 2.5
 * 
 * Inject this into any browser page (via bookmarklet, extension, or console)
 * to join the Clawdia gossip mesh. Every Collective contribution is
 * broadcast to up to 3 peer URLs stored in localStorage.
 *
 * Usage:
 *   <script src="/p2p-client.js"></script>
 *   // or
 *   P2PClient.join('http://localhost:8080')  // register with local bridge
 * ========================================================================== */
;(function (global) {
  'use strict';

  const LS_KEY_PEERS = 'clawdia_peers';
  const LS_KEY_LAST_SYNC = 'clawdia_last_sync_ts';
  const GOSSIP_FANOUT = 2;
  const SYNC_INTERVAL_MS = 60000; // 1 minute

  const P2PClient = {
    _peers: [],
    _bridgeUrl: '',
    _intervalId: null,

    /* ── Lifecycle ─────────────────────────────────── */

    /** Join the mesh by registering with a Clawdia Bridge */
    join(bridgeUrl) {
      this._bridgeUrl = bridgeUrl.replace(/\/+$/, '');
      this._loadPeers();
      this._registerSelf();
      this._startSync();
      console.log(`[P2P] Joined mesh via ${bridgeUrl} — ${this._peers.length} peer(s) known`);
      return this;
    },

    /** Leave the mesh (stop sync) */
    leave() {
      if (this._intervalId) {
        clearInterval(this._intervalId);
        this._intervalId = null;
      }
      console.log('[P2P] Left mesh');
    },

    /* ── Peer Management ───────────────────────────── */

    /** Get all known peer URLs */
    getPeers() {
      return [...this._peers];
    },

    /** Add a peer URL (local only — server registration handled separately) */
    addPeer(url) {
      url = url.replace(/\/+$/, '');
      if (!this._peers.includes(url)) {
        this._peers.push(url);
        this._savePeers();
        this._registerWithPeer(url);
        console.log(`[P2P] Added peer: ${url}`);
      }
    },

    /** Remove a peer URL */
    removePeer(url) {
      this._peers = this._peers.filter(p => p !== url);
      this._savePeers();
    },

    /** Set peers from an array */
    setPeers(urls) {
      this._peers = [...new Set(urls.map(u => u.replace(/\/+$/, '')))];
      this._savePeers();
    },

    /* ── Contribution Broadcasting ──────────────────── */

    /** Broadcast a contribution to all known peers + bridge */
    async contribute(data) {
      const payload = {
        event: 'collective',
        origin: this._bridgeUrl,
        gossip_id: this._uuid(),
        forwarded: 0,
        source: data.source || 'p2p-client',
        total_sessions: data.total_sessions || 1,
        total_messages: data.total_messages || 0,
        donation_amount: data.donation_amount || 0,
        timestamp: Date.now(),
        label: data.label || '',
      };

      // 1. Send to local bridge
      try {
        await fetch(`${this._bridgeUrl}/clawdia/collective`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
      } catch (e) {
        console.warn('[P2P] Local bridge unreachable:', e.message);
      }

      // 2. Gossip to peers
      const targets = this._pickRandom(this._peers, GOSSIP_FANOUT);
      for (const url of targets) {
        this._sendToPeer(url, payload);
      }
    },

    /* ── Internal ──────────────────────────────────── */

    _loadPeers() {
      try {
        const raw = localStorage.getItem(LS_KEY_PEERS);
        this._peers = raw ? JSON.parse(raw) : [];
      } catch { this._peers = []; }
    },

    _savePeers() {
      try {
        localStorage.setItem(LS_KEY_PEERS, JSON.stringify(this._peers));
      } catch {}
    },

    _pickRandom(arr, n) {
      const copy = [...arr];
      const result = [];
      for (let i = 0; i < Math.min(n, copy.length); i++) {
        const idx = Math.floor(Math.random() * copy.length);
        result.push(copy.splice(idx, 1)[0]);
      }
      return result;
    },

    _uuid() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
      });
    },

    async _registerSelf() {
      if (!this._bridgeUrl) return;
      try {
        await fetch(`${this._bridgeUrl}/api/v1/peer/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: this._bridgeUrl, label: 'p2p-client' }),
        });
      } catch {}
    },

    async _registerWithPeer(peerUrl) {
      try {
        await fetch(`${peerUrl}/api/v1/peer/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: this._bridgeUrl, label: 'p2p-client' }),
        });
      } catch {}
    },

    async _sendToPeer(url, payload) {
      try {
        const resp = await fetch(`${url}/api/v1/peer/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          console.warn(`[P2P] Peer ${url} responded ${resp.status}`);
        }
      } catch (e) {
        console.warn(`[P2P] Peer ${url} unreachable:`, e.message);
      }
    },

    _startSync() {
      if (this._intervalId) clearInterval(this._intervalId);
      this._intervalId = setInterval(() => this._syncWithPeers(), SYNC_INTERVAL_MS);
      // Also sync immediately
      setTimeout(() => this._syncWithPeers(), 2000);
    },

    async _syncWithPeers() {
      // Fetch peer lists from known peers
      for (const url of this._peers) {
        try {
          const resp = await fetch(`${url}/api/v1/peers`);
          if (resp.ok) {
            const data = await resp.json();
            if (data.peers) {
              const remoteUrls = data.peers.map(p => p.url);
              for (const ru of remoteUrls) {
                if (!this._peers.includes(ru) && ru !== this._bridgeUrl) {
                  this._peers.push(ru);
                }
              }
              this._savePeers();
            }
          }
        } catch {}
      }
    },
  };

  /* ── Auto-init on DOM ready ──────────────────────── */
  if (typeof document !== 'undefined') {
    const bridgeMeta = document.querySelector('meta[name="clawdia-bridge"]');
    if (bridgeMeta) {
      const url = bridgeMeta.getAttribute('content');
      if (url) {
        document.addEventListener('DOMContentLoaded', () => P2PClient.join(url));
      }
    }
  }

  /* ── Export ──────────────────────────────────────── */
  global.P2PClient = P2PClient;

})(typeof window !== 'undefined' ? window : globalThis);

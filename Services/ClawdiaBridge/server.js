const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawn } = require('child_process');
const { WebSocketServer } = require('ws');
const Database = require('better-sqlite3');
const sharp = require('sharp');
const pino = require('pino');
const logger = pino({
  level: 'info',
  transport: {
    target: 'pino/file',
    options: { destination: path.join(__dirname, 'data', 'clawdia.ndjson') }
  }
});

const PORT_PATH = path.resolve(__dirname, '..', '..', 'config', 'ports.json');
const PORTS = JSON.parse(fs.readFileSync(PORT_PATH, 'utf-8'));
const PORT = PORTS.clawdia_bridge;

const EMOTIONAL_DICT_PATH = path.resolve(__dirname, '..', '..', 'config', 'emotional_dictionary.json');
const EMOTIONAL_DICT = fs.existsSync(EMOTIONAL_DICT_PATH)
  ? JSON.parse(fs.readFileSync(EMOTIONAL_DICT_PATH, 'utf-8'))
  : { emotions: {} };

// ─── Absolute path pinning via .clawdia_paths ───────────────────
const CLAWDIA_PATHS_FILE = path.resolve(__dirname, '..', '..', '.clawdia_paths');
const CLAWDIA_PATHS = {};
if (fs.existsSync(CLAWDIA_PATHS_FILE)) {
  const lines = fs.readFileSync(CLAWDIA_PATHS_FILE, 'utf-8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
      const idx = trimmed.indexOf('=');
      CLAWDIA_PATHS[trimmed.slice(0, idx).trim()] = trimmed.slice(idx + 1).trim();
    }
  }
}

const PUBLIC_DIR = CLAWDIA_PATHS['CLAWDIA_BRIDGE_PUBLIC'] || path.join(__dirname, 'public');
const TICK_MS = 100;

// ─── Persistence ────────────────────────────────────────────────
const DATA_DIR = path.join(__dirname, 'data');
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const LOG_FILE = path.join(DATA_DIR, 'clawdia.log');
const DB_FILE = path.join(DATA_DIR, 'clawdia.db');
const db = new Database(DB_FILE);

db.exec(`
  CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'unknown',
    type TEXT DEFAULT 'response',
    text TEXT NOT NULL DEFAULT '',
    forward_to TEXT,
    acked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_messages_source ON messages(source);
  CREATE INDEX IF NOT EXISTS idx_messages_forward_to ON messages(forward_to);
  CREATE INDEX IF NOT EXISTS idx_messages_acked ON messages(acked);
`);

const insertStmt = db.prepare(`
  INSERT INTO messages (id, timestamp, source, type, text, forward_to)
  VALUES (?, ?, ?, ?, ?, ?)
`);

const insertMany = db.transaction((entries) => {
  for (const e of entries) insertStmt.run(e.id, e.timestamp, e.source, e.type || 'response', e.text, e.forward_to || null);
});

function logToFile(entry) {
  const line = JSON.stringify(entry) + '\n';
  fs.appendFile(LOG_FILE, line, () => {});
}

function persistMessage(entry) {
  try {
    insertStmt.run(entry.id, entry.timestamp, entry.source, entry.type || 'response', entry.text, entry.forward_to || null);
  } catch (e) {
    logger.error({ db: 'insert', error: e.message });
  }
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.wav': 'audio/wav',
  '.mp3': 'audio/mpeg',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.mp4': 'video/mp4',
};

// ─── Audio Pipeline Init ─────────────────────────────────────────
const AUDIO_DIR = path.join(DATA_DIR, 'audio');
if (!fs.existsSync(AUDIO_DIR)) fs.mkdirSync(AUDIO_DIR, { recursive: true });

db.exec(`
  CREATE TABLE IF NOT EXISTS skills_catalog (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'general',
    description TEXT NOT NULL DEFAULT '',
    file_path TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'clawdia',
    api_endpoint TEXT NOT NULL DEFAULT '',
    tested INTEGER NOT NULL DEFAULT 0,
    public INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS collective_sessions (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'unknown',
    session_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    donation_amount REAL DEFAULT 0,
    ip_hash TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS peers (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    label TEXT DEFAULT '',
    trust_score INTEGER DEFAULT 50,
    last_seen TEXT,
    contributed INTEGER DEFAULT 0,
    failed_pings INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS audio_queue (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'unknown',
    text TEXT NOT NULL DEFAULT '',
    emotion TEXT DEFAULT 'neutral',
    intensity REAL DEFAULT 1.0,
    file_path TEXT NOT NULL,
    duration REAL DEFAULT 0,
    played INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS immutable_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    action TEXT NOT NULL,
    trust_delta INTEGER NOT NULL DEFAULT 0,
    penalty_multiplier INTEGER DEFAULT 1,
    amount REAL DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now')),
    previous_hash TEXT NOT NULL DEFAULT '',
    proof_hash TEXT NOT NULL,
    salt TEXT NOT NULL
  );
`);

function getPrevLedgerHash() {
  const row = db.prepare('SELECT proof_hash FROM immutable_ledger ORDER BY id DESC LIMIT 1').get();
  return row ? row.proof_hash : '0'.repeat(64);
}

// Trust protocol migrations (safe for existing DBs)
try { db.exec("ALTER TABLE collective_sessions ADD COLUMN trust_score INTEGER DEFAULT 50"); } catch {}
try { db.exec("ALTER TABLE collective_sessions ADD COLUMN payment_misses INTEGER DEFAULT 0"); } catch {}
try { db.exec("ALTER TABLE collective_sessions ADD COLUMN banned_until TEXT"); } catch {}
try { db.exec("ALTER TABLE collective_sessions ADD COLUMN required_unlock_fee REAL DEFAULT 0"); } catch {}
try { db.exec("ALTER TABLE collective_sessions ADD COLUMN penalty_multiplier INTEGER DEFAULT 1"); } catch {}
try { db.exec("ALTER TABLE collective_sessions ADD COLUMN last_seen TEXT"); } catch {}
try { db.exec("CREATE INDEX IF NOT EXISTS idx_ledger_session ON immutable_ledger(session_id)"); } catch {}
try { db.exec("CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON immutable_ledger(timestamp)"); } catch {}

const insertAudioStmt = db.prepare(`
  INSERT INTO audio_queue (id, timestamp, source, text, emotion, intensity, file_path, duration)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

const VOICE_SERVER = 'http://localhost:8888';
const VOICE_MAP = {
  claude: process.env.CLAWDIA_VOICE_CLAUDE || 'MClEFoImJXBTgLwdLI5n',
  deepseek: process.env.CLAWDIA_VOICE_DEEPSEEK || 'bIHbv24MWmeRgasZH58o',
  gemini: process.env.CLAWDIA_VOICE_GEMINI || 'bIHbv24MWmeRgasZH58o',
  chatgpt: process.env.CLAWDIA_VOICE_CHATGPT || 'bIHbv24MWmeRgasZH58o',
};

const clawdiaInbox = [];
const targetQueues = new Map();
const INBOX_MAX = 500;
const MAX_BODY_BYTES = 512 * 1024;
const MAX_TEXT_LENGTH = 100000;
const RATE_WINDOW_MS = 1000;
const RATE_MAX_PER_WINDOW = 20;
const rateBuckets = new Map();
const LEDGER_PREV_HASH_KEY = 'immutable_ledger:last_hash';

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        req.destroy();
        reject(new Error('body too large'));
        return;
      }
      body += chunk;
    });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); }
      catch { resolve(null); }
    });
    req.on('error', () => resolve(null));
  });
}

function checkRateLimit(source) {
  const now = Date.now();
  if (!rateBuckets.has(source)) rateBuckets.set(source, []);
  const bucket = rateBuckets.get(source);
  const cutoff = now - RATE_WINDOW_MS;
  while (bucket.length && bucket[0] < cutoff) bucket.shift();
  if (bucket.length >= RATE_MAX_PER_WINDOW) return false;
  bucket.push(now);
  return true;
}

function sanitizeText(text) {
  if (typeof text !== 'string') return '';
  if (text.length > MAX_TEXT_LENGTH) return text.slice(0, MAX_TEXT_LENGTH) + '... [truncated]';
  return text;
}

function parseUrl(url) {
  const idx = url.indexOf('?');
  if (idx === -1) return { path: url, params: {} };
  const path = url.slice(0, idx);
  const params = {};
  for (const part of url.slice(idx + 1).split('&')) {
    const [k, v] = part.split('=').map(decodeURIComponent);
    params[k] = v;
  }
  return { path, params };
}

// ─── Image Transform Engine ─────────────────────────────────────────
const IMAGE_DIR = path.join(__dirname, 'images');
if (!fs.existsSync(IMAGE_DIR)) fs.mkdirSync(IMAGE_DIR, { recursive: true });

const TRANSFORM_MODELS = {
  'gray': { fn: 'toGrayscale', desc: 'Convert to grayscale' },
  'blur': { fn: 'applyBlur', desc: 'Gaussian blur' },
  'sharpen': { fn: 'applySharpen', desc: 'Sharpening' },
  'threshold': { fn: 'applyThreshold', desc: 'Binary threshold' },
  'negate': { fn: 'applyNegate', desc: 'Invert colors' },
  'resize': { fn: 'applyResize', desc: 'Resize image' },
  'rotate': { fn: 'applyRotate', desc: 'Rotate image' },
  'normalize': { fn: 'applyNormalize', desc: 'Normalize contrast' },
  'median': { fn: 'applyMedian', desc: 'Median filter (denoise)' },
  'clahe': { fn: 'applyClahe', desc: 'CLAHE contrast enhancement' },
};

async function processImageTransform(data) {
  const { model, params, image: imageBase64 } = data;
  if (!model) throw new Error('model is required');
  if (!imageBase64) throw new Error('image is required (base64)');

  const imgBuf = Buffer.from(imageBase64, 'base64');
  const pipeline = sharp(imgBuf);

  let resultPath, format;
  const modelKey = model.toLowerCase();

  // Local Sharp transforms
  switch (modelKey) {
    case 'gray':
      pipeline.toColorspace('b-w');
      format = 'png';
      break;
    case 'blur': {
      const sigma = (params && params.sigma) || 1.5;
      pipeline.blur(sigma);
      format = 'png';
      break;
    }
    case 'sharpen': {
      const sigma = (params && params.sigma) || 2.0;
      const amount = (params && params.amount) || 1.0;
      pipeline.sharpen(sigma, amount, params && params.threshold);
      format = 'png';
      break;
    }
    case 'threshold': {
      const threshold = (params && params.threshold) || 128;
      pipeline.toColorspace('b-w').threshold(threshold);
      format = 'png';
      break;
    }
    case 'negate':
      pipeline.negate();
      format = 'png';
      break;
    case 'resize': {
      const w = (params && params.width) || null;
      const h = (params && params.height) || null;
      if (w || h) pipeline.resize(w, h, { fit: params && params.fit || 'cover' });
      format = 'png';
      break;
    }
    case 'rotate':
      pipeline.rotate((params && params.angle) || 90);
      format = 'png';
      break;
    case 'normalize':
      pipeline.normalize();
      format = 'png';
      break;
    case 'median': {
      const size = (params && params.size) || 3;
      pipeline.median(size);
      format = 'png';
      break;
    }
    case 'clahe': {
      // Sharp doesn't support CLAHE natively; fall through to Python
      return await runPythonTransform(imgBuf, modelKey, params || {});
    }
    default: {
      // Delegate to Python subprocess for advanced transforms
      return await runPythonTransform(imgBuf, modelKey, params || {});
    }
  }

  const ts = Date.now();
  const outName = `transform_${modelKey}_${ts}.${format}`;
  resultPath = path.join(IMAGE_DIR, outName);
  await pipeline.toFile(resultPath);

  const meta = await sharp(imgBuf).metadata();
  const outMeta = await sharp(resultPath).metadata();

  // Log to skills_catalog as usage
  db.prepare(`UPDATE skills_catalog SET tested = tested + 1 WHERE name = ?`).run(modelKey);

  return {
    ok: true,
    model: modelKey,
    file: `/api/v1/image/file/${outName}`,
    format,
    inputSize: { w: meta.width, h: meta.height },
    outputSize: { w: outMeta.width, h: outMeta.height },
    params: params || {},
  };
}

async function runPythonTransform(imgBuf, modelKey, params) {
  const ts = Date.now();
  const inName = `input_${ts}.png`;
  const outName = `transform_${modelKey}_${ts}.png`;
  const inPath = path.join(IMAGE_DIR, inName);
  const outPath = path.join(IMAGE_DIR, outName);

  fs.writeFileSync(inPath, imgBuf);

  const visualLabPy = path.join(__dirname, '..', '..', 'artifacts', 'visual-lab');
  const script = path.join(visualLabPy, 'unr_transform.py');

  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    const proc = spawn('python', [script, inPath, outPath, modelKey, JSON.stringify(params)], {
      cwd: visualLabPy,
      timeout: 60000,
    });
    proc.stdout.on('data', d => stdout += d.toString());
    proc.stderr.on('data', d => stderr += d.toString());
    proc.on('close', code => {
      if (code !== 0) {
        // Fallback: Python not available, return input unchanged
        try {
          const fallbackPath = path.join(IMAGE_DIR, outName);
          fs.copyFileSync(inPath, fallbackPath);
          const meta = sharp(imgBuf);
          resolve({
            ok: true,
            model: modelKey,
            file: `/api/v1/image/file/${outName}`,
            format: 'png',
            warning: `Python transform unavailable (code ${code}), returned input`,
            stderr: stderr.slice(0, 200),
            params,
          });
        } catch {
          reject(new Error(`Python transform failed: ${stderr.slice(0, 300)}`));
        }
        return;
      }
      resolve({
        ok: true,
        model: modelKey,
        file: `/api/v1/image/file/${outName}`,
        format: 'png',
        stdout: stdout.trim().slice(0, 200),
        params,
      });
    });
    proc.on('error', () => {
      // Python not installed or script missing — return input as fallback
      try {
        const fallbackPath = path.join(IMAGE_DIR, outName);
        fs.copyFileSync(inPath, fallbackPath);
        resolve({
          ok: true,
          model: modelKey,
          file: `/api/v1/image/file/${outName}`,
          format: 'png',
          warning: 'Python not available, returned original',
          params,
        });
      } catch {
        reject(new Error('Python transform unavailable'));
      }
    });
  });
}

function seedSkillsCatalog() {
  const skillsDir = path.join(__dirname, 'Clawdia Skills');
  if (!fs.existsSync(skillsDir)) return;
  const files = fs.readdirSync(skillsDir).filter(f => f.endsWith('.md'));
  const insert = db.prepare(`INSERT OR IGNORE INTO skills_catalog (name, category, description, file_path, source, api_endpoint)
    VALUES (?, ?, ?, ?, ?, ?)`);
  const update = db.prepare(`UPDATE skills_catalog SET category = ?, description = ?, file_path = ?, api_endpoint = ? WHERE name = ?`);
  for (const file of files) {
    const name = file.replace('.md', '');
    const content = fs.readFileSync(path.join(skillsDir, file), 'utf-8');
    const titleMatch = content.match(/^# (.+)$/m);
    const descMatch = content.match(/^## Principle\s*\n\s*(.+)$/m);
    const title = titleMatch ? titleMatch[1].trim() : name;
    const desc = descMatch ? descMatch[1].trim() : 'Image processing skill from the UNR audio-motif library';
    const category = 'image-processing';
    const apiEndpoint = `/api/v1/image/transform?model=${name}`;
    const filePath = `Clawdia Skills/${file}`;
    insert.run(name, category, desc, filePath, 'unr-core', apiEndpoint);
    update.run(category, desc, filePath, apiEndpoint, name);
  }
}

// Seed on startup
seedSkillsCatalog();

// Register local peers from env or default
const seedPeers = (process.env.CLAWDIA_PEERS || `http://localhost:${PORTS.ide_api}`).split(',').map(s => s.trim());
for (const peerUrl of seedPeers) {
  try {
    db.prepare('INSERT OR IGNORE INTO peers (url, label, trust_score) VALUES (?, ?, ?)').run(peerUrl, 'seed', 70);
  } catch {}
}

// ─── P2P Gossip Helpers ─────────────────────────────────────────────
const GOSSIP_FANOUT = 2;
const GOSSIP_MAX_FORWARD = 3;
const gossipMemo = new Set();

function getAlivePeers() {
  return db.prepare("SELECT url FROM peers WHERE last_seen > datetime('now', '-7 day') ORDER BY trust_score DESC").all();
}

function broadcastToPeers(eventData) {
  const peers = getAlivePeers();
  if (peers.length === 0) return;
  const selected = peers.sort(() => Math.random() - 0.5).slice(0, GOSSIP_FANOUT);
  const payload = JSON.stringify({
    event: 'collective',
    origin: `http://localhost:${PORT}`,
    ...eventData,
    gossip_id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
    forwarded: 0,
  });
  for (const peer of selected) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    fetch(peer.url.replace(/\/+$/, '') + '/api/v1/peer/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      signal: controller.signal,
    }).then(r => {
      clearTimeout(timeout);
      if (r.ok) {
        db.prepare('UPDATE peers SET last_seen = datetime(\'now\'), contributed = contributed + 1, failed_pings = 0 WHERE url = ?').run(peer.url);
        logger.info({ p2p: 'gossiped', peer: peer.url });
      } else {
        db.prepare('UPDATE peers SET failed_pings = failed_pings + 1 WHERE url = ?').run(peer.url);
        logger.warn({ p2p: 'peer_error', peer: peer.url, status: r.status });
      }
    }).catch(() => {
      clearTimeout(timeout);
      db.prepare('UPDATE peers SET failed_pings = failed_pings + 1 WHERE url = ?').run(peer.url);
      logger.warn({ p2p: 'peer_unreachable', peer: peer.url });
    });
  }
}

function forwardToPeers(eventData, excludeOrigin) {
  const gossipId = eventData.gossip_id;
  const forwarded = (eventData.forwarded || 0) + 1;
  if (gossipMemo.has(gossipId) || forwarded > GOSSIP_MAX_FORWARD) return;
  gossipMemo.add(gossipId);
  if (gossipMemo.size > 1000) gossipMemo.clear();

  const peers = getAlivePeers().filter(p => p.url !== excludeOrigin);
  if (peers.length === 0) return;
  const selected = peers.sort(() => Math.random() - 0.5).slice(0, GOSSIP_FANOUT);
  const payload = JSON.stringify({ ...eventData, forwarded, origin: `http://localhost:${PORT}` });

  for (const peer of selected) {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 5000);
    fetch(peer.url.replace(/\/+$/, '') + '/api/v1/peer/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      signal: controller.signal,
    }).catch(() => {});
  }
}

function enforceTrust(sessionId) {
  if (!sessionId) return { allowed: true, reason: 'new-session' };
  const row = db.prepare('SELECT trust_score, banned_until, required_unlock_fee, donation_amount FROM collective_sessions WHERE id = ?').get(sessionId);
  if (!row) return { allowed: true, reason: 'new-session' };
  const banned = row.banned_until && new Date(row.banned_until) > new Date();
  if (banned || (row.trust_score || 0) < 10) {
    const unlockFee = row.required_unlock_fee || (row.donation_amount || 0) * 2 || 100;
    return {
      allowed: false,
      reason: banned ? 'banned' : 'low-trust',
      trust_score: row.trust_score || 0,
      required_unlock_fee: unlockFee,
      banned_until: row.banned_until,
      message: banned ? 'Session banned. Contribute to unlock.' : 'Trust score too low. Contribute to increase.',
    };
  }
  return { allowed: true, reason: 'ok', trust_score: row.trust_score };
}

const httpServer = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-session-id');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const { path: urlPath, params: urlParams } = parseUrl(req.url);

  if (req.method === 'POST' && urlPath === '/clawdia') {
    readBody(req).then(data => {
      if (!data) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'invalid body' }));
        return;
      }
      const source = data.source || 'unknown';

      // Rate limit check — protective look-ahead limiter
      if (!checkRateLimit(source)) {
        res.writeHead(429, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'rate limited', retry_ms: RATE_WINDOW_MS }));
      }

      // Sanitize text — prevent abuse at input boundary
      if (data.text) data.text = sanitizeText(data.text);

      const entry = { timestamp: Date.now(), id: Date.now(), acked: false, ...data };

      // Persist to SQLite + log file
      persistMessage(entry);
      logToFile(entry);

      // Route to target queue if forward_to is set
      if (entry.forward_to) {
        const target = entry.forward_to;
        if (!targetQueues.has(target)) targetQueues.set(target, []);
        const q = targetQueues.get(target);
        q.push(entry);
        if (q.length > INBOX_MAX) q.shift();
        logger.info({ clawdia: 'forward', target, source: entry.source, text_preview: (entry.text || '').slice(0, 80) });
        broadcast({ type: 'clawdia', data: { ...entry, queued_for: target } });
      }

      // Always store in general inbox
      clawdiaInbox.push(entry);
      if (clawdiaInbox.length > INBOX_MAX) clawdiaInbox.shift();

      logger.info({ clawdia: 'received', source: entry.source, text_preview: (entry.text || '').slice(0, 80) });
      broadcast({ type: 'clawdia', data: entry });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, id: entry.id }));
    });
    return;
  }

  if (req.method === 'GET' && urlPath === '/clawdia/inbox') {
      const target = urlParams.target;
      const ack = urlParams.ack;

      if (target) {
        let q = targetQueues.get(target) || [];
        if (ack) {
          const ackId = parseInt(ack);
          const idx = q.findIndex(e => e.id === ackId);
          if (idx !== -1) {
            const removed = q.splice(idx, 1)[0];
            removed.acked = true;
            db.prepare('UPDATE messages SET acked = 1 WHERE id = ?').run(ackId);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ ok: true, acked: removed }));
          }
          res.writeHead(200, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ ok: false, error: 'not found' }));
        }
        // Auto-ack: return oldest and remove it atomically
        if (q.length > 0) {
          const oldest = q.shift();
          oldest.acked = true;
          db.prepare('UPDATE messages SET acked = 1 WHERE id = ?').run(oldest.id);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify([oldest]));
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify([]));
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify(clawdiaInbox));
  }

  if (req.method === 'GET' && urlPath === '/clawdia/db') {
    const target = urlParams.target;
    const source = urlParams.source;
    const limit = Math.min(parseInt(urlParams.limit) || 50, 500);
    let sql = 'SELECT * FROM messages WHERE 1=1';
    const params = [];
    if (target) { sql += ' AND forward_to = ?'; params.push(target); }
    if (source) { sql += ' AND source = ?'; params.push(source); }
    sql += ' ORDER BY timestamp DESC LIMIT ?';
    params.push(limit);
    try {
      const rows = db.prepare(sql).all(...params);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify(rows));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: e.message }));
    }
  }

  if (req.method === 'POST' && urlPath === '/clawdia/process') {
    readBody(req).then(data => {
      const { files, commands, message } = data || {};
      const results = { files: [], commands: [] };
      const targetDir = path.resolve(__dirname, 'output');

      if (files && Array.isArray(files)) {
        for (const f of files) {
          if (!f.path || f.content === undefined) continue;
          const fullPath = path.resolve(targetDir, f.path);
          if (!fullPath.startsWith(targetDir)) {
            results.files.push({ path: f.path, status: 'rejected', error: 'path traversal' });
            continue;
          }
          try {
            const dir = path.dirname(fullPath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            fs.writeFileSync(fullPath, f.content, 'utf-8');
            results.files.push({ path: f.path, status: 'written' });
          } catch (e) {
            results.files.push({ path: f.path, status: 'error', error: e.message });
          }
        }
      }

      if (commands && Array.isArray(commands)) {
        const { execSync } = require('child_process');
        for (const cmd of commands) {
          try {
            const out = execSync(cmd, { cwd: targetDir, timeout: 30000, encoding: 'utf-8', maxBuffer: 1024 * 64 });
            results.commands.push({ command: cmd, status: 'ok', output: out.slice(0, 500) });
          } catch (e) {
            results.commands.push({ command: cmd, status: 'error', output: (e.stdout || e.message || '').slice(0, 500) });
          }
        }
      }

      logger.info({ clawdia: 'processed', files: results.files.length, commands: results.commands.length });
      broadcast({ type: 'clawdia_result', data: { id: data.id, results } });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, results }));
    });
    return;
  }

  // ─── Collective Intelligence ───────────────────────────────────
  if (req.method === 'POST' && urlPath === '/clawdia/collective') {
    readBody(req).then(data => {
      if (!data || !data.sessions) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'sessions required' }));
      }
      const sid = req.headers['x-session-id'] || data.sessionId;
      const trustCheck = enforceTrust(sid);
      if (!trustCheck.allowed) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: trustCheck.message, unlock_fee: trustCheck.required_unlock_fee, trust_score: trustCheck.trust_score }));
      }
      const id = Date.now();
      const source = data.source || 'unknown';
      const donation = data.donation_amount || 0;
      const stmt = db.prepare('INSERT INTO collective_sessions (id, source, session_count, message_count, donation_amount, ip_hash, trust_score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'))');
      const trustScore = Math.min(100, 50 + (data.total_sessions || 0) * 2 + (data.total_messages || 0) + donation * 2);
      stmt.run(id, source, data.total_sessions || 0, data.total_messages || 0, donation, '', trustScore);
      // Log to immutable ledger
      const salt = crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString('hex');
      const prevHash = getPrevLedgerHash();
      const proofHash = crypto.createHash('sha256').update(`${prevHash}:${id}:${source}:${trustScore}:${donation}:${salt}`).digest('hex');
      db.prepare('INSERT INTO immutable_ledger (session_id, action, trust_delta, amount, salt, previous_hash, proof_hash) VALUES (?, ?, ?, ?, ?, ?, ?)').run(String(id), 'contribute', trustScore - 50, donation, salt, prevHash, proofHash);
      // Generate recommendation based on session data
      let recommendation = 'Thank you for contributing to the Collective!';
      const services = [];
      if (data.total_messages > 10) services.push('Intent-to-Spec');
      if (data.total_messages > 5) services.push('Text Transformation');
      services.push('Audio Transformation', 'Image Transformation', 'AI Companion');
      const topService = services[Math.floor(Math.random() * services.length)];
      recommendation = 'Based on your ' + data.total_sessions + ' sessions (' + data.total_messages + ' msgs), try our ' + topService + ' API. ' + (data.donation_amount > 0 ? 'Your $' + data.donation_amount + ' boost prioritizes your requests.' : 'Donate $1+ to prioritize future requests.');
      logToFile({ type: 'collective', id, source: data.source, sessions: data.total_sessions, donation: data.donation_amount });
      logger.info({ collective: 'contribution', source: data.source, sessions: data.total_sessions, donation: data.donation_amount });
      broadcast({ type: 'collective', data: { id, source: data.source, total_sessions: data.total_sessions, donation: data.donation_amount } });
      // Gossip to peer mesh
      broadcastToPeers({
        type: 'collective',
        source: data.source || 'unknown',
        total_sessions: data.total_sessions || 0,
        total_messages: data.total_messages || 0,
        donation_amount: data.donation_amount || 0,
        id,
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        ok: true, id,
        recommendation: recommendation,
        services: ['text', 'audio', 'image', 'video', 'companion'],
        donation_url: 'https://paypal.me/clawdia',
        package_url: 'mailto:clawdia@localhost?subject=Package%20Inquiry',
        contributed: true,
      }));
    });
    return;
  }

  // ─── Trust Protocol ───────────────────────────────────────────────
  if (req.method === 'GET' && urlPath === '/api/v1/trust/check') {
    const sessionId = req.headers['x-session-id'] || urlParams.session_id;
    if (!sessionId) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: 'x-session-id header required' }));
    }
    const row = db.prepare('SELECT trust_score, payment_misses, banned_until, required_unlock_fee, penalty_multiplier FROM collective_sessions WHERE id = ?').get(sessionId);
    if (!row) {
      // New session: default trust
      return res.end(JSON.stringify({ score: 50, status: 'new', trust_score: 50, payment_misses: 0, banned_until: null, required_unlock_fee: 0 }));
    }
    const banned = row.banned_until && new Date(row.banned_until) > new Date();
    const status = banned ? 'banned' : row.trust_score >= 70 ? 'trusted' : row.trust_score >= 40 ? 'cautious' : row.trust_score >= 20 ? 'watched' : 'probation';
    const rateLimit = Math.max(1, Math.floor((row.trust_score || 50) / 10));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      score: row.trust_score || 50,
      status,
      trust_score: row.trust_score || 50,
      payment_misses: row.payment_misses || 0,
      banned_until: row.banned_until,
      required_unlock_fee: row.required_unlock_fee || 0,
      penalty_multiplier: row.penalty_multiplier || 1,
      rate_limit_per_hour: rateLimit,
    }));
  }

  if (req.method === 'POST' && urlPath === '/api/v1/trust/penalty') {
    readBody(req).then(data => {
      const { session_id } = data;
      if (!session_id) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'session_id required' }));
      }
      const row = db.prepare('SELECT trust_score, payment_misses, penalty_multiplier, donation_amount FROM collective_sessions WHERE id = ?').get(session_id);
      if (!row) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'session not found' }));
      }
      const newMisses = (row.payment_misses || 0) + 1;
      const newTrust = Math.max(0, (row.trust_score || 50) - 20 * newMisses);
      const banUntil = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
      const unlockFee = (row.donation_amount || 0) * 2;
      db.prepare('UPDATE collective_sessions SET trust_score = ?, payment_misses = ?, banned_until = ?, required_unlock_fee = ?, penalty_multiplier = penalty_multiplier * 2 WHERE id = ?').run(newTrust, newMisses, banUntil, unlockFee, session_id);
      const salt = crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString('hex');
      const prevHash = getPrevLedgerHash();
      const proofHash = crypto.createHash('sha256').update(`${prevHash}:penalty:${session_id}:${newTrust}:${unlockFee}:${salt}`).digest('hex');
      db.prepare('INSERT INTO immutable_ledger (session_id, action, trust_delta, amount, salt, previous_hash, proof_hash, penalty_multiplier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)').run(String(session_id), 'penalty', -20 * newMisses, unlockFee, salt, prevHash, proofHash, 2);
      logger.warn({ trust: 'penalty', session_id, newTrust, unlockFee });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, trust_score: newTrust, banned_until: banUntil, required_unlock_fee: unlockFee }));
    });
    return;
  }

  if (req.method === 'GET' && urlPath === '/api/v1/trust/ledger') {
    const limit = Math.min(parseInt(urlParams.limit) || 50, 500);
    const rows = db.prepare('SELECT * FROM immutable_ledger ORDER BY id DESC LIMIT ?').all(limit);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ entries: rows, count: rows.length }));
  }

  if (req.method === 'GET' && urlPath.startsWith('/api/v1/trust/ledger/')) {
    const sessionId = urlPath.replace('/api/v1/trust/ledger/', '');
    const rows = db.prepare('SELECT * FROM immutable_ledger WHERE session_id = ? ORDER BY id DESC').all(sessionId);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ entries: rows, count: rows.length }));
  }

  // ─── P2P Mesh Endpoints ──────────────────────────────────────────
  if (req.method === 'POST' && urlPath === '/api/v1/peer/register') {
    readBody(req).then(data => {
      if (!data || !data.url) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'url required' }));
      }
      try {
        const u = new URL(data.url);
        if (!['http:', 'https:'].includes(u.protocol)) throw new Error('bad protocol');
      } catch {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'invalid url' }));
      }
      const existing = db.prepare('SELECT id, failed_pings FROM peers WHERE url = ?').get(data.url);
      if (existing) {
        db.prepare('UPDATE peers SET last_seen = datetime(\'now\'), failed_pings = 0, label = COALESCE(NULLIF(?, \'\'), label) WHERE url = ?').run(data.label || '', data.url);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: true, peer_id: existing.id, status: 're-registered' }));
      }
      const stmt = db.prepare('INSERT INTO peers (url, label, trust_score) VALUES (?, ?, ?)');
      stmt.run(data.url, data.label || '', data.trust_score || 50);
      const peerId = db.prepare('SELECT id FROM peers WHERE url = ?').get(data.url).id;
      logger.info({ p2p: 'peer_registered', url: data.url, peerId });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, peer_id: peerId, status: 'registered' }));
    });
    return;
  }

  if (req.method === 'POST' && urlPath === '/api/v1/peer/sync') {
    readBody(req).then(data => {
      if (!data || !data.event) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'event required' }));
      }
      // Log the incoming peer contribution
      const origin = data.origin || 'unknown';
      logger.info({ p2p: 'event_received', event: data.event, origin });
      // Broadcast to local WebSocket clients
      broadcast({ type: 'p2p_sync', data: { ...data, relayed_by: `clawdia:${PORT}` } });
      // Forward to 2 random other peers (anti-entropy gossip)
      forwardToPeers(data, origin);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, relayed: true }));
    });
    return;
  }

  if (req.method === 'GET' && urlPath === '/api/v1/peers') {
    const rows = db.prepare('SELECT id, url, label, trust_score, last_seen, contributed, failed_pings FROM peers ORDER BY trust_score DESC').all();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ peers: rows, count: rows.length }));
  }

  if (req.method === 'GET' && urlPath === '/api/v1/peer/status') {
    const count = db.prepare('SELECT COUNT(*) as c FROM peers').get().c;
    const alive = db.prepare("SELECT COUNT(*) as c FROM peers WHERE last_seen > datetime('now', '-1 day')").get().c;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ total: count, alive, mesh_ready: count >= 2 }));
  }

  if (req.method === 'DELETE' && urlPath.startsWith('/api/v1/peer/')) {
    const peerUrl = decodeURIComponent(urlPath.replace('/api/v1/peer/', ''));
    db.prepare('DELETE FROM peers WHERE url = ?').run(peerUrl);
    logger.info({ p2p: 'peer_removed', peer: peerUrl });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ ok: true }));
  }

  // ─── Audio Pipeline ────────────────────────────────────────────
  if (req.method === 'POST' && urlPath === '/audio/synthesize') {
    readBody(req).then(async data => {
      if (!data || !data.text) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'text required' }));
      }
      const text = sanitizeText(data.text);
      const source = data.source || 'clawdia';
      const emotion = data.emotion || 'neutral';
      const intensity = parseFloat(data.intensity) || 1.0;

      const emotionKey = Object.keys(EMOTIONAL_DICT.emotions || {}).find(
        k => k.toLowerCase() === emotion.toLowerCase()
      );
      const facialDeltas = emotionKey ? EMOTIONAL_DICT.emotions[emotionKey].deltas : {};
      const voiceId = data.voice_id || VOICE_MAP[source] || null;

      try {
        // Step 1: Call voice-server to synthesize raw audio
        const synthRes = await fetch(`${VOICE_SERVER}/synthesize`, {
          method: 'POST', signal: AbortSignal.timeout(60000),
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, voice_id: voiceId }),
        });
        if (!synthRes.ok) throw new Error(`synthesis failed: ${synthRes.status}`);
        const rawAudio = Buffer.from(await synthRes.arrayBuffer());
        const rawFormat = synthRes.headers.get('x-format') || 'wav';
        const rawExt = rawFormat === 'mp3' ? '.mp3' : '.wav';
        const rawPath = path.join(AUDIO_DIR, `raw-${Date.now()}${rawExt}`);
        fs.writeFileSync(rawPath, rawAudio);

        // Step 2: Run through SAAS transposer
        const morphedPath = path.join(AUDIO_DIR, `morphed-${Date.now()}.wav`);
        const transposerScript = path.join(__dirname, 'transposer.py');
        let duration = 0;
        if (fs.existsSync(transposerScript)) {
          try {
            const safeEmotion = (emotion || 'neutral').replace(/[^a-zA-Z0-9_-]/g, '');
            const safeIntensity = parseFloat(intensity) || 1.0;
            const result = execSync(
              `py -3 "${transposerScript}" "${rawPath}" "${morphedPath}" --emotion "${safeEmotion}" --intensity ${safeIntensity}`,
              { timeout: 30000, windowsHide: true, encoding: 'utf-8', maxBuffer: 1024 * 64 }
            );
            const parsed = JSON.parse(result);
            duration = parsed.samples / parsed.sr;
          } catch {
            // If transposer fails, use raw audio
            fs.copyFileSync(rawPath, morphedPath);
          }
        } else {
          fs.copyFileSync(rawPath, morphedPath);
        }

        // Step 3: Store in database
        const id = Date.now();
        const ts = id;
        insertAudioStmt.run(id, ts, source, text.slice(0, 200), emotion, intensity, morphedPath, duration);
        try { fs.unlinkSync(rawPath); } catch {}

        // Step 4: Broadcast to WebSocket clients
        broadcast({ type: 'audio_new', data: { id, source, text_preview: text.slice(0, 80), emotion, intensity, duration, timestamp: ts } });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, id, source, emotion, intensity, duration, facial_deltas: facialDeltas }));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  if (req.method === 'GET' && urlPath === '/audio/inbox') {
    const rows = db.prepare('SELECT id, timestamp, source, text, emotion, intensity, duration, played FROM audio_queue ORDER BY timestamp DESC LIMIT 50').all();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify(rows));
  }

  if (req.method === 'GET' && urlPath.startsWith('/audio/file/')) {
    const id = parseInt(urlPath.replace('/audio/file/', ''));
    const row = db.prepare('SELECT file_path FROM audio_queue WHERE id = ?').get(id);
    if (!row || !fs.existsSync(row.file_path)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('Not Found');
    }
    const ext = path.extname(row.file_path);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'audio/wav', 'Content-Length': fs.statSync(row.file_path).size });
    fs.createReadStream(row.file_path).pipe(res);
    return;
  }

  if (req.method === 'POST' && urlPath.startsWith('/audio/ack/')) {
    const id = parseInt(urlPath.replace('/audio/ack/', ''));
    db.prepare('UPDATE audio_queue SET played = 1 WHERE id = ?').run(id);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ ok: true }));
  }

  // ─── Image Transform API ──────────────────────────────────────────
  if (req.method === 'POST' && urlPath === '/api/v1/image/transform') {
    readBody(req).then(async data => {
      if (!data) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'invalid body' }));
      }
      const sid = req.headers['x-session-id'] || (data && data.session_id);
      const trustCheck = enforceTrust(sid);
      if (!trustCheck.allowed) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: trustCheck.message, unlock_fee: trustCheck.required_unlock_fee }));
      }
      try {
        const result = await processImageTransform(data);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  // ─── Skills Catalog API ────────────────────────────────────────────
  if (req.method === 'GET' && urlPath === '/api/v1/skills') {
    const rows = db.prepare('SELECT * FROM skills_catalog ORDER BY name').all();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify(rows));
  }

  if (req.method === 'GET' && urlPath.startsWith('/api/v1/skills/')) {
    const skillName = urlPath.replace('/api/v1/skills/', '');
    const row = db.prepare('SELECT * FROM skills_catalog WHERE name = ?').get(skillName);
    if (!row) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: 'skill not found' }));
    }
    const skillPath = path.join(__dirname, 'Clawdia Skills', skillName + '.md');
    try {
      const content = fs.readFileSync(skillPath, 'utf-8');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ...row, content }));
    } catch {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ...row, content: '' }));
    }
  }

  if (req.method === 'POST' && urlPath === '/api/v1/skills/seed') {
    seedSkillsCatalog();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ ok: true }));
  }

  // ─── Serve processed images ────────────────────────────────────────
  if (req.method === 'GET' && urlPath.startsWith('/api/v1/image/file/')) {
    const name = path.basename(urlPath.replace('/api/v1/image/file/', ''));
    const imgPath = path.join(__dirname, 'images', name);
    if (!fs.existsSync(imgPath)) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: 'file not found' }));
    }
    const ext = path.extname(name).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    fs.createReadStream(imgPath).pipe(res);
    return;
  }

  if (req.method === 'GET' && urlPath === '/config/ports') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify(PORTS));
  }

  if (req.method === 'GET' && urlPath === '/config/emotional-dictionary') {
    if (!fs.existsSync(EMOTIONAL_DICT_PATH)) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: 'emotional dictionary not found' }));
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify(EMOTIONAL_DICT));
  }

  let filePath = path.join(PUBLIC_DIR, req.url === '/' ? 'index.html' : req.url);
  const ext = path.extname(filePath);

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

const wss = new WebSocketServer({ server: httpServer });

let state = {
  pumpRunning: false,
  pumpSpeed: 0,
  pressure: 0,
  flowRate: 0,
  tankLevel: 65,
  valveOpen: true,
  temperature: 28,
  power: 0,
};

function resetFaults() {
  state.pumpRunning = false;
  state.pumpSpeed = 0;
}

function simulate() {
  const tick = TICK_MS / 1000;

  if (state.pumpRunning) {
    state.pumpSpeed = Math.min(100, state.pumpSpeed + 8 * tick);
    const pct = state.pumpSpeed / 100;
    state.pressure = pct * 10 * (0.92 + 0.16 * Math.random());
    state.flowRate = pct * 60 * (0.93 + 0.14 * Math.random());
    state.power = pct * 75 * (0.96 + 0.08 * Math.random());
    state.temperature = 28 + pct * 32 + 4 * Math.random();

    if (state.valveOpen) {
      state.tankLevel -= 0.4 * pct * tick;
    } else {
      state.pressure += 0.02;
      if (state.pressure > 14) {
        broadcast({ type: 'alert', data: { severity: 'critical', message: 'OVERPRESSURE — auto shutdown' } });
        resetFaults();
      }
    }
  } else {
    state.pumpSpeed = Math.max(0, state.pumpSpeed - 20 * tick);
    state.pressure *= Math.pow(0.9, tick);
    state.flowRate *= Math.pow(0.85, tick);
    state.power *= Math.pow(0.7, tick);
    state.temperature += (25 - state.temperature) * 0.02 * tick;
  }

  state.tankLevel = Math.max(0, Math.min(100, state.tankLevel));
  if (state.tankLevel < 5) {
    broadcast({ type: 'alert', data: { severity: 'warning', message: 'TANK LOW — refill needed' } });
  }

  broadcast({ type: 'telemetry', data: { ...state } });
}

let simInterval = setInterval(simulate, TICK_MS);

const clients = new Set();

wss.on('connection', (ws, req) => {
  clients.add(ws);
  logger.info({ ws: 'client_connected', total: clients.size });

    ws.on('close', () => {
      clients.delete(ws);
      logger.info({ ws: 'client_disconnected', total: clients.size });
  });

  ws.on('error', () => clients.delete(ws));
});

function handleCommand(msg, ws) {
  const { action, value } = msg.data || {};

  switch (action) {
    case 'start_pump':
      if (state.tankLevel < 3) {
        ws.send(JSON.stringify({ type: 'error', data: { message: 'Cannot start — tank level critically low' } }));
        return;
      }
      state.pumpRunning = true;
      broadcast({ type: 'event', data: { level: 'info', message: 'Pump started' } });
      break;

    case 'stop_pump':
      state.pumpRunning = false;
      broadcast({ type: 'event', data: { level: 'info', message: 'Pump stopped' } });
      break;

    case 'set_speed':
      state.pumpSpeed = Math.max(0, Math.min(100, value || 0));
      if (state.pumpSpeed === 0) state.pumpRunning = false;
      broadcast({ type: 'event', data: { level: 'info', message: `Speed set to ${Math.round(state.pumpSpeed)}%` } });
      break;

    case 'toggle_valve':
      state.valveOpen = !state.valveOpen;
      broadcast({ type: 'event', data: { level: 'info', message: `Valve ${state.valveOpen ? 'opened' : 'closed'}` } });
      break;

    case 'set_tank':
      state.tankLevel = Math.max(0, Math.min(100, value || 0));
      broadcast({ type: 'event', data: { level: 'info', message: `Tank level set to ${Math.round(state.tankLevel)}%` } });
      break;

    default:
      ws.send(JSON.stringify({ type: 'error', data: { message: `unknown action: ${action}` } }));
  }
}

function broadcast(msg) {
  const raw = JSON.stringify(msg);
  for (const ws of clients) {
    if (ws.readyState === 1) {
      ws.send(raw);
    }
  }
}

httpServer.listen(PORT, () => {
  logger.info({ server: 'started', port: PORT });
  logger.info('WebSocket server ready');
});

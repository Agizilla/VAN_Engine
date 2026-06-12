import http from 'http';
import { readFileSync, existsSync, writeFileSync, unlinkSync, mkdirSync } from 'fs';
import { homedir, tmpdir } from 'os';
import { join, dirname, extname } from 'path';
import { spawn, execSync } from 'child_process';
import { fileURLToPath } from 'url';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const PORTS = JSON.parse(readFileSync(join(SCRIPT_DIR, 'config', 'ports.json'), 'utf-8'));
const PORT = PORTS.voice_server;

const EMOTIONAL_DICT_PATH = join(SCRIPT_DIR, 'config', 'emotional_dictionary.json');
const EMOTIONAL_DICT = existsSync(EMOTIONAL_DICT_PATH) ? JSON.parse(readFileSync(EMOTIONAL_DICT_PATH, 'utf-8')) : { emotions: {} };
const RATE_LIMIT = 10;
const RATE_WINDOW = 60_000;
const MAX_TEXT_LENGTH = 500;

function sanitize(text) {
  return text
    .replace(/<script/gi, '').replace(/\.\.\//g, '')
    .replace(/[;&|><`$\\]/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1').replace(/#{1,6}\s+/g, '')
    .trim().substring(0, MAX_TEXT_LENGTH);
}

const requestCounts = new Map();
function checkRateLimit(key) {
  const now = Date.now();
  const record = requestCounts.get(key);
  if (!record || now > record.resetTime) {
    requestCounts.set(key, { count: 1, resetTime: now + RATE_WINDOW });
    return true;
  }
  if (record.count >= RATE_LIMIT) return false;
  record.count++;
  return true;
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => { try { resolve(JSON.parse(body)); } catch { reject(new Error('Invalid JSON')); } });
  });
}

function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function parseMultipart(body, boundary) {
  const parts = {};
  const bodyStr = body.toString('latin1');
  const delimiter = '--' + boundary;
  const rawParts = bodyStr.split(delimiter);
  let runningOffset = 0;
  for (const raw of rawParts) {
    runningOffset = bodyStr.indexOf(raw, runningOffset);
    if (raw.includes('\r\n\r\n') && !raw.includes('--\r\n')) {
      const idx = raw.indexOf('\r\n\r\n');
      const headerRaw = raw.substring(0, idx);
      const headerByteLen = Buffer.byteLength(raw.substring(0, idx + 4), 'latin1');
      const dataStart = runningOffset + headerByteLen;
      let dataEnd = body.length;
      // Find the next boundary marker after this part
      const nextMarker = bodyStr.indexOf('\r\n--' + boundary, runningOffset + 1);
      if (nextMarker > 0) dataEnd = nextMarker;
      const data = body.subarray(dataStart, dataEnd);
      const nameMatch = headerRaw.match(/name="([^"]+)"/);
      const filenameMatch = headerRaw.match(/filename="([^"]+)"/);
      if (nameMatch) {
        const name = nameMatch[1];
        if (filenameMatch) {
          parts[name] = { filename: filenameMatch[1], data, isFile: true };
        } else {
          parts[name] = { data: data.toString('utf-8').trim(), isFile: false };
        }
      }
    }
  }
  return parts;
}

function sayViaSAPI(text) {
  return new Promise((resolve) => {
    const escaped = text.replace(/'/g, "''").replace(/"/g, '`"');
    const cp = spawn('powershell', [
      '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
      `Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SelectVoiceByHints('Female'); $s.Speak('${escaped}')`,
    ], { windowsHide: true });
    cp.on('error', (e) => { console.error('SAPI error:', e.message); resolve(false); });
    cp.on('exit', () => resolve(true));
  });
}

function sayViaLocalTTS(text) {
  return new Promise((resolve) => {
    const tmpFile = join(tmpdir(), `voice-${Date.now()}.wav`);
    const ttsScript = join(SCRIPT_DIR, 'tts_local.py');
    if (!existsSync(ttsScript)) { resolve(false); return; }

    const python = process.env.PYTHON_PATH || join(homedir(), '.pyenv', 'pyenv-win', 'versions', '3.10.11', 'python.exe');
    const cp = spawn(python, [ttsScript, '--text', text, '--output', tmpFile], {
      cwd: SCRIPT_DIR,
      windowsHide: true,
      stdio: 'pipe',
    });

    let stderr = '';
    cp.stderr.on('data', d => stderr += d);

    cp.on('exit', (code) => {
      if (code !== 0 || !existsSync(tmpFile)) {
        console.error('Local TTS failed:', stderr);
        resolve(false);
        return;
      }
      const player = spawn('powershell', [
        '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
        `(New-Object Media.SoundPlayer '${tmpFile.replace(/'/g, "''")}').PlaySync()`,
      ], { windowsHide: true });
      player.on('exit', () => {
        setTimeout(() => { try { unlinkSync(tmpFile); } catch {} }, 3000);
        resolve(true);
      });
      player.on('error', () => {
        setTimeout(() => { try { unlinkSync(tmpFile); } catch {} }, 3000);
        resolve(false);
      });
    });
    cp.on('error', () => resolve(false));
  });
}

async function speakViaElevenLabs(text, voiceId) {
  try {
    const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
      method: 'POST',
      headers: { 'Accept': 'audio/mpeg', 'Content-Type': 'application/json', 'xi-api-key': process.env.ELEVENLABS_API_KEY },
      body: JSON.stringify({
        text, model_id: 'eleven_turbo_v2_5',
        voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.0, speed: 1.0, use_speaker_boost: true },
      }),
    });
    if (!res.ok) return null;
    const audio = Buffer.from(await res.arrayBuffer());
    const tmpFile = join(tmpdir(), `voice-${Date.now()}.mp3`);
    writeFileSync(tmpFile, audio);
    await new Promise((resolve) => {
      const cp = spawn('powershell', [
        '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
        `$p = New-Object -ComObject WMPlayer.OCX; $p.URL = '${tmpFile.replace(/'/g, "''")}'; $p.controls.play(); Start-Sleep -Seconds 300; $p.close()`,
      ], { windowsHide: true });
      cp.on('exit', () => { setTimeout(() => { try { unlinkSync(tmpFile); } catch {} }, 5000); resolve(); });
    });
    return { status: 'played', engine: 'elevenlabs', voice_id: voiceId };
  } catch { return null; }
}

async function synthesizeToFile(text, voiceId, outputPath) {
  const s = sanitize(text);
  if (!s) return null;

  const engine = voiceId || 'auto';

  // Try ElevenLabs first (returns audio buffer directly)
  if (engine === 'elevenlabs' || (engine === 'auto' && process.env.ELEVENLABS_API_KEY)) {
    try {
      const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId || 'fTtv3eikoepIosk8dTZ5'}`, {
        method: 'POST',
        headers: { 'Accept': 'audio/mpeg', 'Content-Type': 'application/json', 'xi-api-key': process.env.ELEVENLABS_API_KEY },
        body: JSON.stringify({
          text: s, model_id: 'eleven_turbo_v2_5',
          voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.0, speed: 1.0, use_speaker_boost: true },
        }),
      });
      if (res.ok) {
        const audio = Buffer.from(await res.arrayBuffer());
        writeFileSync(outputPath, audio);
        return { file: outputPath, format: 'mp3', engine: 'elevenlabs', size: audio.length };
      }
    } catch {}
  }

  // Try local TTS (generates WAV)
  if (engine === 'local' || engine === 'styletts2' || engine === 'auto') {
    const ttsScript = join(SCRIPT_DIR, 'tts_local.py');
    if (existsSync(ttsScript)) {
      try {
        const python = process.env.PYTHON_PATH || 'py';
        execSync(`"${python}" -3 "${ttsScript}" --text "${s.replace(/"/g, '\\"')}" --output "${outputPath}"`, {
          timeout: 30000, windowsHide: true, stdio: 'pipe',
        });
        if (existsSync(outputPath)) {
          return { file: outputPath, format: 'wav', engine: 'local', size: readFileSync(outputPath).length };
        }
      } catch {}
    }
  }

  // Fallback: SAPI → capture to WAV
  try {
    const wavPath = outputPath.replace(/\.\w+$/, '.wav');
    const psScript = `
      Add-Type -AssemblyName System.Speech;
      $s = New-Object System.Speech.Synthesis.SpeechSynthesizer;
      $s.SetOutputToWaveFile('${wavPath.replace(/'/g, "''")}');
      $s.Speak('${s.replace(/'/g, "''")}');
      $s.Dispose();
    `;
    execSync(`powershell -NoProfile -WindowStyle Hidden -Command "${psScript.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`, {
      timeout: 60000, windowsHide: true, stdio: 'pipe',
    });
    if (existsSync(wavPath)) {
      return { file: wavPath, format: 'wav', engine: 'sapi', size: readFileSync(wavPath).length };
    }
  } catch {}

  return null;
}

async function speak(text, voiceId) {
  const s = sanitize(text);
  if (!s) return { status: 'skipped', reason: 'empty after sanitization' };

  const engine = voiceId || 'auto';

  if (engine === 'local' || engine === 'styletts2') {
    const ok = await sayViaLocalTTS(s);
    if (ok) return { status: 'played', engine: 'local', voice_id: 'amelia1-ft' };
    console.error('Local TTS failed, falling back');
  }

  if (engine === 'elevenlabs' || (engine === 'auto' && process.env.ELEVENLABS_API_KEY)) {
    const result = await speakViaElevenLabs(s, engine === 'elevenlabs' ? 'fTtv3eikoepIosk8dTZ5' : 'fTtv3eikoepIosk8dTZ5');
    if (result) return result;
  }

  await sayViaSAPI(s);
  return { status: 'played', engine: 'sapi', voice_id: 'windows-default' };
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  if (req.url === '/health' || (req.url === '/notify' && req.method === 'GET')) {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      local_tts: existsSync(join(SCRIPT_DIR, 'tts_local.py')),
      engines: {
        elevenlabs: !!process.env.ELEVENLABS_API_KEY,
        local: existsSync(join(SCRIPT_DIR, 'tts_local.py')),
        sapi: true,
      },
      emotional_dictionary: {
        version: EMOTIONAL_DICT.version || 'none',
        emotions_count: Object.keys(EMOTIONAL_DICT.emotions || {}).length,
      },
    }));
    return;
  }

  // ─── Synthesize endpoint (returns audio file) ───
  if (req.url === '/synthesize' && req.method === 'POST') {
    try {
      const body = await getBody(req);
      const { message, voice_id, emotion } = body || {};
      if (!message) { res.writeHead(400); res.end(JSON.stringify({ error: 'message required' })); return; }
      const tmpFile = join(tmpdir(), `clawdia-synth-${Date.now()}.wav`);
      const result = await synthesizeToFile(message, voice_id, tmpFile);
      if (!result) { res.writeHead(500); res.end(JSON.stringify({ error: 'synthesis failed' })); return; }
      const audio = readFileSync(result.file);
      if (result.file !== tmpFile) unlinkSync(result.file);
      const emotionName = emotion || 'neutral';
      const emotionKey = Object.keys(EMOTIONAL_DICT.emotions || {}).find(
        k => k.toLowerCase() === emotionName.toLowerCase()
      );
      const facialDeltas = emotionKey ? EMOTIONAL_DICT.emotions[emotionKey].deltas : {};
      res.writeHead(200, {
        'Content-Type': result.format === 'mp3' ? 'audio/mpeg' : 'audio/wav',
        'Content-Length': audio.length,
        'X-Engine': result.engine,
        'X-Format': result.format,
        'X-Emotion': emotionName,
        'X-Facial-Deltas': JSON.stringify(facialDeltas),
      });
      res.end(audio);
    } catch (e) {
      res.writeHead(500); res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  // ─── Clone endpoint (receives audio + voice name from SAAS recorder) ───
  if (req.url === '/clone' && req.method === 'POST') {
    try {
      const ct = req.headers['content-type'] || '';
      const boundary = ct.includes('boundary=') ? ct.split('boundary=')[1].trim() : null;
      if (!boundary) { res.writeHead(400); res.end(JSON.stringify({ error: 'multipart/form-data required' })); return; }

      const raw = await getRawBody(req);
      const parts = parseMultipart(raw, boundary);

      if (!parts.audio || !parts.audio.isFile) { res.writeHead(400); res.end(JSON.stringify({ error: 'audio file required' })); return; }
      const name = parts.name ? parts.name.data : 'custom_voice';
      const emotions = parts.emotions ? parts.emotions.data : '[]';
      const source = parts.source ? parts.source.data : 'saas';

      // Write audio to temp file
      const ext = parts.audio.filename ? extname(parts.audio.filename) : '.wav';
      const audioPath = join(tmpdir(), `clone-${name}-${Date.now()}${ext}`);
      writeFileSync(audioPath, parts.audio.data);

      const modelsDir = join(SCRIPT_DIR, 'models', 'cloned');
      if (!existsSync(modelsDir)) mkdirSync(modelsDir, { recursive: true });

      // Default transcript based on emotion tags
      let transcript = 'This is a voice sample for cloning.';
      try {
        const emoArr = JSON.parse(emotions);
        if (Array.isArray(emoArr) && emoArr.length > 0) {
          transcript = `This is a ${emoArr.join(' ')} voice sample. My voice carries these emotions naturally.`;
        }
      } catch {}

      // Spawn train_voice.py
      console.log(`🧬 Cloning voice "${name}" from ${audioPath} (emotions: ${emotions})`);

      const python = process.env.PYTHON_PATH || 'py';
      const trainScript = join(SCRIPT_DIR, 'train_voice.py');
      let cloneSuccess = false;

      if (existsSync(trainScript)) {
        try {
          execSync(`"${python}" -3 "${trainScript}" --name "${name}" --wav "${audioPath}" --text "${transcript.replace(/"/g, '\\"')}"`, {
            timeout: 120000, windowsHide: true, stdio: 'pipe',
          });
          cloneSuccess = true;
        } catch (e) {
          console.error('Clone training failed:', e.message);
        }
      }

      // Clean up temp audio
      setTimeout(() => { try { unlinkSync(audioPath); } catch {} }, 5000);

      const modelPath = join(modelsDir, name);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      if (cloneSuccess) {
        console.log(`✅ Voice "${name}" cloned successfully`);
        res.end(JSON.stringify({ status: 'ok', model_path: modelPath, voice_name: name, emotions: emotions }));
      } else {
        // Even if training fails, save the raw audio for manual processing
        const savedPath = join(modelsDir, `${name}_source${ext}`);
        writeFileSync(savedPath, parts.audio.data);
        console.log(`⚠️ Voice "${name}" audio saved (training skipped). Model pending.`);
        res.end(JSON.stringify({
          status: 'ok', model_path: savedPath, voice_name: name, emotions: emotions,
          warning: 'Training pipeline unavailable. Raw audio saved. Use train_voice.py manually.',
        }));
      }
    } catch (e) {
      console.error('/clone error:', e);
      res.writeHead(500); res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  if (req.url !== '/notify' || req.method !== 'POST') {
    res.writeHead(404); res.end('Not found');
    return;
  }

  try {
    const body = await getBody(req);
    const { message, voice_id, voice_enabled } = body;

    if (!message) { res.writeHead(400); res.end(JSON.stringify({ error: 'message required' })); return; }
    if (voice_enabled === false) { res.writeHead(200); res.end(JSON.stringify({ status: 'skipped' })); return; }
    if (!checkRateLimit(req.socket.remoteAddress || 'local')) { res.writeHead(429); res.end(JSON.stringify({ error: 'rate limited' })); return; }

    const result = await speak(message, voice_id);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(result));
  } catch (err) {
    console.error('Server error:', err);
    res.writeHead(500); res.end(JSON.stringify({ error: err.message }));
  }
});

async function start() {
  server.listen(PORT, () => {
    console.log(`Voice server running on http://localhost:${PORT}`);
    const engines = [];
    if (process.env.ELEVENLABS_API_KEY) engines.push('ElevenLabs');
    if (existsSync(join(SCRIPT_DIR, 'tts_local.py'))) engines.push('Local StyleTTS2');
    engines.push('Windows SAPI (fallback)');
    console.log(`TTS engines: ${engines.join(', ')}`);
  });
}

start();

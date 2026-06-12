#!/usr/bin/env node
const [message, voiceId = 'auto'] = process.argv.slice(2);
if (!message) { console.error('Usage: node voice-notify.mjs "message" [voice_id: auto|local|sapi|elevenlabs]'); process.exit(1); }

const s = message.replace(/<script/gi,'').replace(/\.\.\//g,'').replace(/[;&|><`$\\]/g,'')
  .replace(/\*\*([^*]+)\*\*/g,'$1').replace(/\*([^*]+)\*/g,'$1')
  .replace(/`([^`]+)`/g,'$1').replace(/#{1,6}\s+/g,'').trim().substring(0,500);

if (!s) { console.log('Empty after sanitization'); process.exit(0); }
const { spawn } = await import('child_process');
const { tmpdir, homedir } = await import('os');
const { join, dirname } = await import('path');
const { writeFileSync, unlinkSync, existsSync } = await import('fs');
const { fileURLToPath } = await import('url');
const __dirname = dirname(fileURLToPath(import.meta.url));

function sapiSpeak(text) {
  return new Promise(r => {
    const cp = spawn('powershell', ['-NoProfile', '-WindowStyle', 'Hidden', '-Command',
      `Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.SelectVoiceByHints('Female'); $synth.Speak('${text.replace(/'/g, "''")}')`],
      { windowsHide: true });
    cp.on('exit', () => r());
  });
}

function localTTS(text) {
  return new Promise(r => {
    const tmpFile = join(tmpdir(), `voice-${Date.now()}.wav`);
    const ttsScript = join(__dirname, 'tts_local.py');
    if (!existsSync(ttsScript)) { r(false); return; }
    const python = process.env.PYTHON_PATH || join(homedir(), '.pyenv', 'pyenv-win', 'versions', '3.10.11', 'python.exe');
    const cp = spawn(python, [ttsScript, '--text', text, '--output', tmpFile], { windowsHide: true, stdio: 'pipe' });
    cp.on('exit', code => {
      if (code !== 0 || !existsSync(tmpFile)) { r(false); return; }
      const player = spawn('powershell', ['-NoProfile', '-WindowStyle', 'Hidden', '-Command',
        `(New-Object Media.SoundPlayer '${tmpFile.replace(/'/g, "''")}').PlaySync()`], { windowsHide: true });
      player.on('exit', () => { setTimeout(() => { try { unlinkSync(tmpFile); } catch {} }, 3000); r(true); });
      player.on('error', () => { setTimeout(() => { try { unlinkSync(tmpFile); } catch {} }, 3000); r(false); });
    });
  });
}

async function elevenLabs(text) {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) return false;
  try {
    const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/fTtv3eikoepIosk8dTZ5`, {
      method: 'POST',
      headers: { 'Accept': 'audio/mpeg', 'Content-Type': 'application/json', 'xi-api-key': key },
      body: JSON.stringify({ text, model_id: 'eleven_turbo_v2_5', voice_settings: { stability: 0.5, similarity_boost: 0.75 } }),
    });
    if (!res.ok) return false;
    const audio = Buffer.from(await res.arrayBuffer());
    const tmpFile = join(tmpdir(), `voice-${Date.now()}.mp3`);
    writeFileSync(tmpFile, audio);
    await new Promise(r => {
      const cp = spawn('powershell', ['-NoProfile', '-WindowStyle', 'Hidden', '-Command',
        `$p = New-Object -ComObject WMPlayer.OCX; $p.URL = '${tmpFile.replace(/'/g, "''")}'; $p.controls.play(); Start-Sleep -Seconds 300; $p.close()`],
        { windowsHide: true });
      cp.on('exit', () => { setTimeout(() => { try { unlinkSync(tmpFile); } catch {} }, 5000); r(); });
    });
    return true;
  } catch { return false; }
}

const engine = voiceId.toLowerCase();
if (engine === 'local' || engine === 'styletts2' || engine === 'auto') {
  const ok = await localTTS(s);
  if (ok) { console.log(`[Local TTS] ${s.substring(0, 60)}`); process.exit(0); }
  if (engine !== 'auto') { console.log('Local TTS unavailable, trying fallbacks...'); }
}

if (engine === 'elevenlabs' || engine === 'auto') {
  const ok = await elevenLabs(s);
  if (ok) { console.log(`[ElevenLabs] ${s.substring(0, 60)}`); process.exit(0); }
}

await sapiSpeak(s);
console.log(`[SAPI] ${s.substring(0, 60)}`);

import { app } from 'electron';
import { spawn } from 'child_process';
import { readFileSync, existsSync, writeFileSync, unlinkSync } from 'fs';
import { homedir, tmpdir } from 'os';
import { join } from 'path';

interface PronunciationEntry {
  term: string;
  phonetic: string;
  note?: string;
}

interface CompiledRule {
  regex: RegExp;
  phonetic: string;
}

interface VoiceEntry {
  voiceId: string;
  voiceName?: string;
  stability: number;
  similarity_boost: number;
  style: number;
  speed: number;
  use_speaker_boost: boolean;
  volume: number;
}

interface ElevenLabsSettings {
  stability: number;
  similarity_boost: number;
  style?: number;
  speed?: number;
  use_speaker_boost?: boolean;
}

const EMOTIONAL_PRESETS: Record<string, { stability: number; similarity_boost: number }> = {
  excited: { stability: 0.7, similarity_boost: 0.9 },
  celebration: { stability: 0.65, similarity_boost: 0.85 },
  insight: { stability: 0.55, similarity_boost: 0.8 },
  creative: { stability: 0.5, similarity_boost: 0.75 },
  success: { stability: 0.6, similarity_boost: 0.8 },
  progress: { stability: 0.55, similarity_boost: 0.75 },
  investigating: { stability: 0.6, similarity_boost: 0.85 },
  debugging: { stability: 0.55, similarity_boost: 0.8 },
  learning: { stability: 0.5, similarity_boost: 0.75 },
  pondering: { stability: 0.65, similarity_boost: 0.8 },
  focused: { stability: 0.7, similarity_boost: 0.85 },
  caution: { stability: 0.4, similarity_boost: 0.6 },
  urgent: { stability: 0.3, similarity_boost: 0.9 },
};

const FALLBACK_SETTINGS: ElevenLabsSettings = {
  stability: 0.5,
  similarity_boost: 0.75,
  style: 0.0,
  speed: 1.0,
  use_speaker_boost: true,
};

const EMOJI_MAP: Record<string, string> = {
  '\u{1F4A5}': 'excited',
  '\u{1F389}': 'celebration',
  '\u{1F4A1}': 'insight',
  '\u{1F3A8}': 'creative',
  '\u{2728}': 'success',
  '\u{1F4C8}': 'progress',
  '\u{1F50D}': 'investigating',
  '\u{1F41B}': 'debugging',
  '\u{1F4DA}': 'learning',
  '\u{1F914}': 'pondering',
  '\u{1F3AF}': 'focused',
  '\u{26A0}\u{FE0F}': 'caution',
  '\u{1F6A8}': 'urgent',
};

export class VoiceService {
  private pronunciationRules: CompiledRule[] = [];
  private apiKey: string;
  private defaultVoiceId: string;
  private requestCounts = new Map<string, { count: number; resetTime: number }>();
  private readonly RATE_LIMIT = 10;
  private readonly RATE_WINDOW = 60_000;

  constructor() {
    this.apiKey = process.env.ELEVENLABS_API_KEY || '';
    this.defaultVoiceId = process.env.ELEVENLABS_VOICE_ID || 's3TPKV1kjDlVtZbl4Ksh';
    this.loadPronunciations();
  }

  private loadPronunciations(): void {
    const candidates = [
      join(app.getAppPath(), '.cide', 'VoiceServer', 'pronunciations.json'),
      join(process.cwd(), '.cide', 'VoiceServer', 'pronunciations.json'),
      join(__dirname, '..', '..', '..', '.cide', 'VoiceServer', 'pronunciations.json'),
    ];

    for (const pronPath of candidates) {
      if (!existsSync(pronPath)) continue;
      try {
        const config = JSON.parse(readFileSync(pronPath, 'utf-8'));
        this.pronunciationRules = (config.replacements || []).map((entry: PronunciationEntry) => ({
          regex: new RegExp(`\\b${this.escapeRegex(entry.term)}\\b`, 'g'),
          phonetic: entry.phonetic,
        }));
        console.log(`[Voice] Loaded ${this.pronunciationRules.length} pronunciation rules from ${pronPath}`);
        return;
      } catch (e) {
        console.warn('[Voice] Failed to load pronunciations:', e);
      }
    }
  }

  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  private applyPronunciations(text: string): string {
    let result = text;
    for (const rule of this.pronunciationRules) {
      result = result.replace(rule.regex, rule.phonetic);
    }
    return result;
  }

  private sanitizeForSpeech(input: string): string {
    return input
      .replace(/<script/gi, '')
      .replace(/\.\.\//g, '')
      .replace(/[;&|><`$\\]/g, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/#{1,6}\s+/g, '')
      .trim()
      .substring(0, 500);
  }

  private extractEmotion(message: string): { cleaned: string; emotion?: string } {
    const emotionMatch = message.match(/\[(\u{1F4A5}|\u{1F389}|\u{1F4A1}|\u{1F3A8}|\u{2728}|\u{1F4C8}|\u{1F50D}|\u{1F41B}|\u{1F4DA}|\u{1F914}|\u{1F3AF}|\u{26A0}\u{FE0F}|\u{1F6A8})\s+(\w+)\]/u);
    if (emotionMatch) {
      const emoji = emotionMatch[1];
      const emotionName = emotionMatch[2].toLowerCase();
      if (EMOJI_MAP[emoji] === emotionName) {
        return { cleaned: message.replace(emotionMatch[0], '').trim(), emotion: emotionName };
      }
    }
    return { cleaned: message };
  }

  private checkRateLimit(key: string): boolean {
    const now = Date.now();
    const record = this.requestCounts.get(key);
    if (!record || now > record.resetTime) {
      this.requestCounts.set(key, { count: 1, resetTime: now + this.RATE_WINDOW });
      return true;
    }
    if (record.count >= this.RATE_LIMIT) return false;
    record.count++;
    return true;
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }

  getStatus(): { configured: boolean; defaultVoiceId: string; pronunciationRules: number } {
    return {
      configured: this.isConfigured(),
      defaultVoiceId: this.defaultVoiceId,
      pronunciationRules: this.pronunciationRules.length,
    };
  }

  async playTTS(text: string, voiceId?: string, voiceSettings?: Partial<ElevenLabsSettings>): Promise<boolean> {
    if (!this.apiKey) return false;

    const safe = this.sanitizeForSpeech(text);
    if (!safe) return false;

    if (!this.checkRateLimit('voice')) {
      console.warn('[Voice] Rate limit exceeded');
      return false;
    }

    const { cleaned, emotion } = this.extractEmotion(safe);
    const pronounced = this.applyPronunciations(cleaned);
    const voice = voiceId || this.defaultVoiceId;

    const settings: ElevenLabsSettings = {
      stability: voiceSettings?.stability ?? FALLBACK_SETTINGS.stability,
      similarity_boost: voiceSettings?.similarity_boost ?? FALLBACK_SETTINGS.similarity_boost,
      style: voiceSettings?.style ?? FALLBACK_SETTINGS.style,
      speed: voiceSettings?.speed ?? FALLBACK_SETTINGS.speed,
      use_speaker_boost: voiceSettings?.use_speaker_boost ?? FALLBACK_SETTINGS.use_speaker_boost,
    };

    if (emotion && EMOTIONAL_PRESETS[emotion]) {
      settings.stability = EMOTIONAL_PRESETS[emotion].stability;
      settings.similarity_boost = EMOTIONAL_PRESETS[emotion].similarity_boost;
    }

    try {
      const url = `https://api.elevenlabs.io/v1/text-to-speech/${voice}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Accept: 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': this.apiKey,
        },
        body: JSON.stringify({
          text: pronounced,
          model_id: 'eleven_turbo_v2_5',
          voice_settings: settings,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error(`[Voice] ElevenLabs API error: ${response.status} - ${errText}`);
        return false;
      }

      const buffer = Buffer.from(await response.arrayBuffer());
      return await this.playAudio(buffer);
    } catch (e: any) {
      console.error('[Voice] TTS error:', e.message);
      return false;
    }
  }

  private async playAudio(buffer: Buffer): Promise<boolean> {
    const tmpFile = join(tmpdir(), `voice-${Date.now()}.mp3`);
    try {
      writeFileSync(tmpFile, buffer);
      const platform = process.platform;

      if (platform === 'win32') {
        return await this.playWindows(tmpFile);
      } else if (platform === 'darwin') {
        return await this.playMacOS(tmpFile);
      } else {
        return await this.playLinux(tmpFile);
      }
    } finally {
      setTimeout(() => {
        try { unlinkSync(tmpFile); } catch { /* ignore */ }
      }, 30_000);
    }
  }

  private playWindows(filePath: string): Promise<boolean> {
    return new Promise((resolve) => {
      const cp = spawn('powershell', [
        '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
        `$p = New-Object -ComObject WMPlayer.OCX; $p.URL = '${filePath.replace(/'/g, "''")}'; $p.controls.play(); Start-Sleep -Seconds 300; $p.close()`,
      ], { windowsHide: true });
      cp.on('error', () => resolve(false));
      cp.on('exit', () => resolve(true));
    });
  }

  private playMacOS(filePath: string): Promise<boolean> {
    return new Promise((resolve) => {
      const cp = spawn('/usr/bin/afplay', [filePath]);
      cp.on('error', () => resolve(false));
      cp.on('exit', () => resolve(true));
    });
  }

  private playLinux(filePath: string): Promise<boolean> {
    return new Promise((resolve) => {
      const players = ['paplay', 'aplay', 'ffplay', 'mpg123'];
      const tryPlay = (index: number) => {
        if (index >= players.length) return resolve(false);
        const cp = spawn(players[index], [filePath]);
        cp.on('error', () => tryPlay(index + 1));
        cp.on('exit', () => resolve(true));
      };
      tryPlay(0);
    });
  }
}

export const voiceService = new VoiceService();

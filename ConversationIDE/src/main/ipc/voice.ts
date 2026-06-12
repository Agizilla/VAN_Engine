import { IpcMain } from 'electron';
import { spawn } from 'child_process';
import { join } from 'path';

const projectRoot = join(__dirname, '..', '..', '..', '..');

interface VoiceStatus {
  configured: boolean;
  voices: string[];
  baseModel: boolean;
}

let status: VoiceStatus = { configured: false, voices: [], baseModel: false };

async function runPython(script: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const proc = spawn('py', ['-3', script, ...args], { cwd: projectRoot });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (data) => { stdout += data.toString(); });
    proc.stderr.on('data', (data) => { stderr += data.toString(); });
    proc.on('close', (code) => {
      if (code === 0) resolve(stdout.trim());
      else reject(new Error(stderr.trim()));
    });
    proc.on('error', reject);
  });
}

export function setupVoiceHandlers(ipcMain: IpcMain): void {
  ipcMain.handle('voice:synthesize', async (_event, params: { text: string; voiceName?: string }) => {
    try {
      const voiceName = params.voiceName || 'male';
      const outputPath = join(projectRoot, `output_${voiceName}_${Date.now()}.wav`);
      await runPython('voice_cloner.py', [
        '--synthesize', params.text,
        '--voice', voiceName,
        '--output', outputPath
      ]);
      return { ok: true, outputPath };
    } catch (err: any) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle('voice:status', async () => {
    return status;
  });

  ipcMain.handle('voice:train', async (_event, params: { name: string; wavPath: string; transcript: string }) => {
    try {
      await runPython('train_voice.py', [
        '--name', params.name,
        '--wav', params.wavPath,
        '--text', params.transcript
      ]);
      return { ok: true };
    } catch (err: any) {
      return { ok: false, error: err.message };
    }
  });

  ipcMain.handle('voice:list', async () => {
    try {
      const output = await runPython('onnx_inference.py', ['--list']);
      return { ok: true, voices: status.voices };
    } catch (err: any) {
      return { ok: false, error: err.message };
    }
  });
}

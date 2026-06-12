import { IpcMain } from 'electron';
import { spawn } from 'child_process';
import * as path from 'path';

export function setupInferenceHandlers(ipcMain: IpcMain): void {
  ipcMain.handle('inference:run', async (_event, params: {
    systemPrompt: string;
    userPrompt: string;
    tier: 'fast' | 'standard' | 'smart';
    expectJson?: boolean;
  }) => {
    const bridgePath = path.join(__dirname, '../../../resources/van_engine_bridge/inference_bridge.py');

    return new Promise((resolve) => {
      const proc = spawn('python', [
        bridgePath,
        '--tier', params.tier,
        '--json',
        params.userPrompt
      ]);

      let output = '';
      proc.stdout.on('data', (data) => { output += data.toString(); });
      proc.on('close', () => {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch {
          resolve({ success: false, error: 'Parse failed', output });
        }
      });
      proc.on('error', (err) => {
        resolve({ success: false, error: err.message });
      });
    });
  });
}

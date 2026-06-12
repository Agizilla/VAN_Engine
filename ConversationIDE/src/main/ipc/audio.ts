import { IpcMain, BrowserWindow } from 'electron';
import { execFile } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..', '..');

function findClawDiaPython(): string | null {
  const candidates = [
    path.join(PROJECT_ROOT, 'ClawDia', '.venv', 'Scripts', 'python.exe'),
    path.join(PROJECT_ROOT, 'ClawDia', '.venv', 'bin', 'python'),
    'python',
  ];
  for (const c of candidates) {
    try {
      if (c === 'python') return 'python';
      if (fs.existsSync(c)) return c;
    } catch { continue; }
  }
  return null;
}

function getSrcPath(): string {
  return path.join(PROJECT_ROOT, 'ClawDia', 'src');
}

export function setupAudioHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('audio:transcribe', async (_event, params: { filePath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.audioSkill import AudioSkill
skill = AudioSkill()
result = skill.transcribe(params["filePath"])
print(json.dumps({"error": None, "result": result}))
`,
        JSON.stringify(params),
      ], { timeout: 120000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('audio:separate-stems', async (_event, params: { filePath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.audioSkill import AudioSkill
skill = AudioSkill()
result = skill.separate_stems(params["filePath"])
print(json.dumps({"error": None, "result": str(result)}))
`,
        JSON.stringify(params),
      ], { timeout: 300000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('audio:synthesize', async (_event, params: { text: string; outputPath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.audioSkill import AudioSkill
skill = AudioSkill()
result = skill.synthesize(params["text"], params["outputPath"])
print(json.dumps({"error": None, "result": str(result)}))
`,
        JSON.stringify(params),
      ], { timeout: 60000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('audio:info', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.audioSkill import AudioSkill
skill = AudioSkill()
meta = skill.get_meta()
caps = skill.get_capabilities()
print(json.dumps({"error": None, "result": {"meta": meta, "capabilities": caps}}))
`,
      ], { timeout: 15000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('audio:classify', async (_event, params: { filePath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.audioSkill import AudioSkill
skill = AudioSkill()
result = skill.classify_sound(params["filePath"])
print(json.dumps({"error": None, "result": result}))
`,
        JSON.stringify(params),
      ], { timeout: 30000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('audio:model-stats', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.audioSkill import AudioSkill
skill = AudioSkill()
result = skill.get_model_stats()
print(json.dumps({"error": None, "result": result}))
`,
      ], { timeout: 15000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  console.log('[Audio] Master skill handlers registered');
}

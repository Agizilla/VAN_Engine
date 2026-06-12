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

export function setupPsychoacousticHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('psychoacoustic:ambient', async (_event, params: { flavor: string; duration?: number }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.psychoacousticSkill import PsychoacousticSkill
skill = PsychoacousticSkill()
result = skill.get_ambient(params["flavor"], params.get("duration", 0.1))
print(json.dumps({"error": None, "result": result.tolist() if hasattr(result, 'tolist') else str(result)}))
`,
        JSON.stringify(params),
      ], { timeout: 30000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('psychoacoustic:sleep-report', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.psychoacousticSkill import PsychoacousticSkill
skill = PsychoacousticSkill()
result = skill.get_sleep_report()
print(json.dumps({"error": None, "result": result}))
`,
      ], { timeout: 15000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('psychoacoustic:morning-report', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.psychoacousticSkill import PsychoacousticSkill
skill = PsychoacousticSkill()
result = skill.get_morning_report()
print(json.dumps({"error": None, "result": result}))
`,
      ], { timeout: 15000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('psychoacoustic:emotion', async (_event, params: { sampleRate?: number }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      execFile(pythonExe, [
        '-c', `
import json, sys, numpy as np
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.psychoacousticSkill import PsychoacousticSkill
skill = PsychoacousticSkill()
dummy = np.random.randn(params.get("sampleRate", 16000)).astype(np.float32) * 0.1
result = skill.detect_emotion(dummy)
print(json.dumps({"error": None, "result": result}))
`,
        JSON.stringify(params),
      ], { timeout: 15000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('psychoacoustic:info', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.psychoacousticSkill import PsychoacousticSkill
skill = PsychoacousticSkill()
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

  console.log('[Psychoacoustic] Master skill handlers registered');
}

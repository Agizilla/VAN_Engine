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

export function setupImageHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('image:detect', async (_event, params: { filePath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.imageSkill import ImageSkill
skill = ImageSkill()
faces = skill.detect_faces(params["filePath"])
print(json.dumps({"error": None, "result": faces}))
`,
        JSON.stringify(params),
      ], { timeout: 60000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('image:segment', async (_event, params: { filePath: string; points?: number[][] }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.imageSkill import ImageSkill
skill = ImageSkill()
mask = skill.segment(params["filePath"], points=params.get("points"))
print(json.dumps({"error": None, "result": str(mask)}))
`,
        JSON.stringify(params),
      ], { timeout: 120000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('image:ocr', async (_event, params: { filePath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.imageSkill import ImageSkill
skill = ImageSkill()
text = skill.ocr(params["filePath"])
print(json.dumps({"error": None, "result": text}))
`,
        JSON.stringify(params),
      ], { timeout: 60000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('image:info', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.imageSkill import ImageSkill
skill = ImageSkill()
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

  console.log('[Image] Master skill handlers registered');
}

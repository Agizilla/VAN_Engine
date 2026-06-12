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

export function setupVideoHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('video:detect-faces', async (_event, params: { filePath: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.videoSkill import VideoSkill
skill = VideoSkill()
faces = skill.detect_faces_in_video(params["filePath"])
print(json.dumps({"error": None, "result": faces}))
`,
        JSON.stringify(params),
      ], { timeout: 120000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('video:trim', async (_event, params: { filePath: string; start: number; end: number; output?: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.videoSkill import VideoSkill
skill = VideoSkill()
result = skill.trim_video(params["filePath"], params["start"], params["end"], output=params.get("output"))
print(json.dumps({"error": None, "result": str(result)}))
`,
        JSON.stringify(params),
      ], { timeout: 300000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('video:gif', async (_event, params: { filePath: string; output?: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.videoSkill import VideoSkill
skill = VideoSkill()
result = skill.make_gif(params["filePath"], output=params.get("output"))
print(json.dumps({"error": None, "result": str(result)}))
`,
        JSON.stringify(params),
      ], { timeout: 120000, maxBuffer: 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, result: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, result: null }); }
      });
    });
  });

  ipcMain.handle('video:info', async () => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', result: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.videoSkill import VideoSkill
skill = VideoSkill()
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

  console.log('[Video] Master skill handlers registered');
}

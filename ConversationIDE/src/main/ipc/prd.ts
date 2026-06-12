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

export function setupPRDHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('prd:scan', async (_event, params: { root?: string } = {}) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', prds: null };
    const srcPath = getSrcPath();
    const scanRoot = params.root || path.join(PROJECT_ROOT, '..', '..');
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from tools.master_skills.prdSkill import PRDSkill
skill = PRDSkill()
prds = skill.scan(${JSON.stringify(scanRoot)})
# Strip raw content to reduce payload size
for p in prds:
    p.pop('raw', None)
    p.pop('section_content', None)
catalog = skill.get_catalog(prds)
print(json.dumps({"error": None, "prds": prds, "catalog": catalog}))
`,
      ], { timeout: 60000, maxBuffer: 10 * 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, prds: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, prds: null }); }
      });
    });
  });

  ipcMain.handle('prd:get', async (_event, params: { slug: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', prd: null };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.prdSkill import PRDSkill
skill = PRDSkill()
prds = skill.scan()
prd = next((p for p in prds if p["slug"] == params["slug"]), None)
print(json.dumps({"error": None, "prd": prd}))
`,
        JSON.stringify(params),
      ], { timeout: 30000, maxBuffer: 5 * 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, prd: null });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, prd: null }); }
      });
    });
  });

  ipcMain.handle('prd:search', async (_event, params: { query: string; root?: string }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) return { error: 'ClawDia Python runtime not found', results: [] };
    const srcPath = getSrcPath();
    return new Promise((resolve) => {
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1])
from tools.master_skills.prdSkill import PRDSkill
skill = PRDSkill()
prds = skill.scan()
results = skill.search(params["query"], prds)
for p in results:
    p.pop('raw', None)
print(json.dumps({"error": None, "results": results, "count": len(results)}))
`,
        JSON.stringify(params),
      ], { timeout: 30000, maxBuffer: 5 * 1024 * 1024 }, (error, stdout) => {
        if (error) return resolve({ error: `Python error: ${error.message}`, results: [] });
        try { resolve(JSON.parse(stdout.trim())); } catch { resolve({ error: `Parse error`, results: [] }); }
      });
    });
  });

  ipcMain.handle('prd:viewer-path', async () => {
    const viewerPath = path.join(PROJECT_ROOT, 'ClawDia', 'src', 'tools', 'master_skills', 'prd_viewer.html');
    return { path: viewerPath, exists: fs.existsSync(viewerPath) };
  });

  console.log('[PRD] Master skill handlers registered');
}

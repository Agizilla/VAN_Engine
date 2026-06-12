import { IpcMain, BrowserWindow } from 'electron';
import { execFile } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..', '..');

function findClawDiaPython(): string | null {
  const candidates = [
    path.join(PROJECT_ROOT, 'ClawDia', '.venv', 'Scripts', 'python.exe'),
    path.join(PROJECT_ROOT, 'ClawDia', '.venv', 'bin', 'python'),
    path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe'),
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

function getClawDiaSrcPath(): string {
  return path.join(PROJECT_ROOT, 'ClawDia', 'src');
}

interface ForgeParams {
  intentText: string;
  description?: string;
  author?: string;
  autoRegister?: boolean;
}

// ─────────────────────────────────────────────────────────────────
// IPC Handlers for Intent → Skill Forging
// ─────────────────────────────────────────────────────────────────

export function setupIntentForgeHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  // Forge a skill from a raw intent string
  ipcMain.handle('intent-forge:forge', async (_event, params: ForgeParams) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) {
      return { error: 'ClawDia Python runtime not found', result: null };
    }

    const srcPath = getClawDiaSrcPath();

    return new Promise((resolve) => {
      const intentArg = params.intentText;
      const authorArg = params.author || 'ClawDia';
      const descArg = params.description || '';
      const autoRegArg = params.autoRegister !== false ? '1' : '0';

      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
from skills.intent_forge import IntentForgeSkill
from skills.signal_filter import SignalFilterSkill
from skills.intent_enricher import IntentEnricherSkill

intent = sys.argv[1] if len(sys.argv) > 1 else ""
author = sys.argv[2] if len(sys.argv) > 2 else "ClawDia"
desc = sys.argv[3] if len(sys.argv) > 3 else ""
auto_reg = sys.argv[4] if len(sys.argv) > 4 else "1"

sf = SignalFilterSkill()
filtered = sf.execute(text=intent)
clean_text = (filtered.get("result") or {}).get("clean_text") or intent

ie = IntentEnricherSkill()
enriched = ie.execute(text=clean_text)
grid = (enriched.get("result") or {}).get("grid") or {}

fi = IntentForgeSkill()
fi.author = author
forged = fi.execute(
    intent_text=intent,
    grid=grid,
    description=desc or (enriched.get("result") or {}).get("intent_summary", intent),
    author=author,
    version="1.0.0",
    auto_register=auto_reg == "1"
)
print(json.dumps({"error": forged.get("error"), "result": forged.get("result")}))
`,
        intentArg,
        authorArg,
        descArg,
        autoRegArg,
      ], {
        timeout: 30000,
        maxBuffer: 1024 * 1024,
      }, (error, stdout, stderr) => {
        if (error) {
          resolve({ error: `Python error: ${error.message}`, stderr: stderr?.substring(0, 500), result: null });
          return;
        }
        const trimmed = stdout.trim();
        if (!trimmed) {
          resolve({ error: 'Python returned empty output', result: null });
          return;
        }
        try {
          const parsed = JSON.parse(trimmed);
          resolve(parsed);
        } catch {
          resolve({ error: `Failed to parse Python output: ${trimmed.substring(0, 500)}`, result: null });
        }
      });
    });
  });

  // List all forged skills
  ipcMain.handle('intent-forge:list', async () => {
    const generatedDir = path.join(PROJECT_ROOT, 'ClawDia', 'src', 'skills', 'generated');
    if (!fs.existsSync(generatedDir)) {
      return { skills: [] };
    }
    const files = fs.readdirSync(generatedDir)
      .filter(f => f.endsWith('.py') && f !== '__init__.py')
      .map(f => {
        const fullPath = path.join(generatedDir, f);
        const stat = fs.statSync(fullPath);
        return {
          name: f.replace(/\.py$/, ''),
          path: fullPath,
          size: stat.size,
          modified: stat.mtime.toISOString(),
        };
      });
    return { skills: files };
  });

  // Get raw code of a forged skill
  ipcMain.handle('intent-forge:get-code', async (_event, skillName: string) => {
    const filePath = path.join(PROJECT_ROOT, 'ClawDia', 'src', 'skills', 'generated', `${skillName}.py`);
    if (!fs.existsSync(filePath)) {
      return { error: `Skill '${skillName}' not found`, content: null };
    }
    return { error: null, content: fs.readFileSync(filePath, 'utf-8') };
  });

  console.log('[IntentForge] Handlers registered');
}

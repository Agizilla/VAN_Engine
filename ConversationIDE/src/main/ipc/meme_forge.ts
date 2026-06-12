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

export function setupMemeForgeHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  // Generate a meme
  ipcMain.handle('meme-forge:generate', async (_event, params: {
    topic?: string; tone?: string; frame?: string; count?: number;
    action?: string; meme_id?: string; tags?: string[];
  }) => {
    const pythonExe = findClawDiaPython();
    if (!pythonExe) {
      return { error: 'ClawDia Python runtime not found', result: null };
    }
    const srcPath = getSrcPath();
    const action = params.action || 'generate';

    return new Promise((resolve) => {
      const args = [JSON.stringify(params), action];
      const child = execFile(pythonExe, [
        '-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(srcPath)})
params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
action = sys.argv[2] if len(sys.argv) > 2 else "generate"

if action == "list_memes":
    from skills.humor_skill import HumorMemeSkill
    s = HumorMemeSkill()
    r = s.execute(action="list")
    print(json.dumps({"error": r.get("error"), "result": r.get("result")}))
elif action == "by_id":
    from skills.humor_skill import HumorMemeSkill
    s = HumorMemeSkill()
    r = s.execute(action="by_id", meme_id=params.get("meme_id", ""))
    print(json.dumps({"error": r.get("error"), "result": r.get("result")}))
else:
    from skills.meme_forge import MemeForgeSkill
    s = MemeForgeSkill()
    kwargs = {k: v for k, v in params.items() if k != "action"}
    kwargs["action"] = action
    r = s.execute(**kwargs)
    print(json.dumps({"error": r.get("error"), "result": r.get("result")}))
`,
        args[0],
        args[1],
      ], {
        timeout: 30000,
        maxBuffer: 1024 * 1024,
      }, (error, stdout, stderr) => {
        if (error) {
          resolve({ error: `Python error: ${error.message}`, result: null });
          return;
        }
        try {
          resolve(JSON.parse(stdout.trim()));
        } catch {
          resolve({ error: `Failed to parse: ${stdout.substring(0, 200)}`, result: null });
        }
      });
    });
  });

  console.log('[MemeForge] Handler registered');
}

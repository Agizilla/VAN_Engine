import { IpcMain, BrowserWindow } from 'electron';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execAsync = promisify(exec);

interface AlgorithmRequest {
  query: string;
  effort?: 'standard' | 'extended' | 'advanced' | 'deep' | 'comprehensive';
  context?: Record<string, any>;
}

interface AlgorithmResponse {
  success: boolean;
  effort: string;
  timeUsedSeconds: number;
  timeBudgetSeconds: number;
  phases: Record<string, any>;
}

export function setupAlgorithmHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('algorithm:execute', async (event, request: AlgorithmRequest): Promise<AlgorithmResponse> => {
    const { query, effort = 'standard', context = {} } = request;

    const engineRoot = process.env.VAN_ENGINE_ROOT || path.join(process.cwd(), 'VAN_Engine');
    const brainPath = path.join(engineRoot, 'VAN', 'brain.py');

    if (!fs.existsSync(brainPath)) {
      throw new Error(`VAN_Engine brain not found at ${brainPath}`);
    }

    const pythonCmd = process.env.PYTHON || 'python';
    const escapedQuery = query.replace(/'/g, "\\'").replace(/"/g, '\\"');
    const script = `
import asyncio
import json
import sys
sys.path.insert(0, '${engineRoot.replace(/\\/g, '/')}')
from VAN.brain import VANEngineBrain

async def main():
    brain = VANEngineBrain.Instance()
    result = await brain.ExecuteAlgorithmQuery("${escapedQuery}", ${JSON.stringify(context)})
    print(json.dumps({
        "success": result.Success,
        "message": result.Message,
        "action": result.Action,
        "algorithm_phase": result.AlgorithmPhase,
        "effort": result.EffortTier,
        "isc_checked": result.ISCChecked,
        "isc_total": result.ISCTotal,
        "data": result.Data
    }))

asyncio.run(main())
    `;

    try {
      const { stdout, stderr } = await execAsync(`"${pythonCmd}"`, ['-c', script]);
      if (stderr) console.warn('[Algorithm] Python stderr:', stderr);

      const result = JSON.parse(stdout);

      window.webContents.send('iso:audit', {
        id: `audit_${Date.now()}`,
        timestamp: Date.now(),
        component: 'algorithm',
        action: `execute:${effort}`
      });

      return {
        success: result.success,
        effort: result.effort || effort,
        timeUsedSeconds: result.data?.time_used_seconds || 0,
        timeBudgetSeconds: result.data?.time_budget_seconds || 0,
        phases: result.data?.phases || {}
      };
    } catch (error: any) {
      console.error('[Algorithm] Execution error:', error);
      throw new Error(`Algorithm execution failed: ${error.message}`);
    }
  });

  ipcMain.handle('algorithm:phase:update', async (event, { slug, phase }: { slug: string; phase: string }) => {
    const engineRoot = process.env.VAN_ENGINE_ROOT || path.join(process.cwd(), 'VAN_Engine');
    const prdPath = path.join(engineRoot, 'memory', 'WORK', slug, 'PRD.md');

    if (fs.existsSync(prdPath)) {
      let content = fs.readFileSync(prdPath, 'utf-8');
      content = content.replace(/^phase: .*/m, `phase: ${phase}`);
      fs.writeFileSync(prdPath, content, 'utf-8');
    }

    window.webContents.send('algorithm:phase-change', {
      phase,
      timestamp: Date.now()
    });
    return { success: true };
  });

  ipcMain.handle('algorithm:prd:list', async () => {
    const engineRoot = process.env.VAN_ENGINE_ROOT || path.join(process.cwd(), 'VAN_Engine');
    const workDir = path.join(engineRoot, 'memory', 'WORK');

    if (!fs.existsSync(workDir)) {
      return { prds: [] };
    }

    const prds = fs.readdirSync(workDir)
      .filter(f => fs.statSync(path.join(workDir, f)).isDirectory())
      .map(slug => {
        const prdPath = path.join(workDir, slug, 'PRD.md');
        if (fs.existsSync(prdPath)) {
          const content = fs.readFileSync(prdPath, 'utf-8');
          const frontmatterMatch = content.match(/^---\n(.*?)\n---/s);
          if (frontmatterMatch) {
            const frontmatter = frontmatterMatch[1];
            const taskMatch = frontmatter.match(/task: (.*)/);
            const phaseMatch = frontmatter.match(/phase: (.*)/);
            const progressMatch = frontmatter.match(/progress: (.*)/);
            return {
              slug,
              task: taskMatch ? taskMatch[1] : slug,
              phase: phaseMatch ? phaseMatch[1] : 'unknown',
              progress: progressMatch ? progressMatch[1] : '0/0',
              updated: fs.statSync(prdPath).mtimeMs
            };
          }
        }
        return { slug, task: slug, phase: 'unknown', progress: '0/0', updated: 0 };
      })
      .sort((a, b) => b.updated - a.updated);

    return { prds };
  });

  ipcMain.handle('algorithm:prd:get', async (event, slug: string) => {
    const engineRoot = process.env.VAN_ENGINE_ROOT || path.join(process.cwd(), 'VAN_Engine');
    const prdPath = path.join(engineRoot, 'memory', 'WORK', slug, 'PRD.md');

    if (!fs.existsSync(prdPath)) {
      throw new Error(`PRD not found: ${slug}`);
    }

    const content = fs.readFileSync(prdPath, 'utf-8');
    return { content, slug };
  });
}

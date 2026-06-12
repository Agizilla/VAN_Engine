import { IpcMain, BrowserWindow } from 'electron';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { BuildRequest } from './protocols';

interface BuildResult {
  success: boolean;
  output: string;
  errors: string[];
  duration: number;
}

function emitAudit(window: BrowserWindow, component: string, action: string) {
  const event = { id: `audit_${Date.now()}`, timestamp: Date.now(), component, action };
  window.webContents.send('iso:audit', event);
}

export function setupBuildHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('build:run', async (event, request: BuildRequest): Promise<BuildResult> => {
    const { projectRoot, target } = request;
    const startTime = Date.now();

    emitAudit(window, 'build', `run:${target}@${projectRoot}`);

    try {
      let output = '';
      const errors: string[] = [];

      switch (target) {
        case 'react':
        case 'vue':
          try {
            output = execSync('npm run build', {
              cwd: projectRoot,
              encoding: 'utf-8',
              timeout: 120000
            });
          } catch (buildErr: any) {
            errors.push(buildErr.message || 'Build failed');
            output = buildErr.stdout || '';
          }
          break;

        case 'python':
          try {
            output = execSync(`${process.env.PYTHON_CMD || 'py'} -m compileall .`, {
              cwd: projectRoot,
              encoding: 'utf-8',
              timeout: 60000
            });
          } catch (buildErr: any) {
            errors.push(buildErr.message || 'Python compile failed');
          }
          break;

        case 'csharp':
          try {
            output = execSync('dotnet build', {
              cwd: projectRoot,
              encoding: 'utf-8',
              timeout: 180000
            });
          } catch (buildErr: any) {
            errors.push(buildErr.message || 'Dotnet build failed');
          }
          break;

        default:
          errors.push(`Unknown target: ${target}`);
      }

      const duration = Date.now() - startTime;
      return {
        success: errors.length === 0,
        output,
        errors,
        duration
      };
    } catch (err: any) {
      return {
        success: false,
        output: '',
        errors: [err.message || 'Unknown build error'],
        duration: Date.now() - startTime
      };
    }
  });

  ipcMain.handle('build:status', async () => {
    return { available: true, lastBuild: null };
  });
}

import { execSync, exec } from 'child_process';
import * as path from 'path';
import { BrowserWindow } from 'electron';

export interface PipelineStage {
  name: string;
  command: string;
  cwd: string;
  timeout?: number;
}

export interface PipelineResult {
  success: boolean;
  stage: string;
  output: string;
  error?: string;
  duration: number;
}

export class BuildPipeline {
  private window: BrowserWindow | null = null;

  setWindow(win: BrowserWindow) {
    this.window = win;
  }

  async run(stages: PipelineStage[]): Promise<PipelineResult[]> {
    const results: PipelineResult[] = [];

    for (const stage of stages) {
      const startTime = Date.now();
      this.emitProgress(stage.name, 'running');

      try {
        const output = execSync(stage.command, {
          cwd: stage.cwd,
          encoding: 'utf-8',
          timeout: stage.timeout || 120000,
          maxBuffer: 10 * 1024 * 1024
        });

        const result: PipelineResult = {
          success: true,
          stage: stage.name,
          output,
          duration: Date.now() - startTime
        };
        results.push(result);
        this.emitProgress(stage.name, 'complete', result);
      } catch (err: any) {
        const result: PipelineResult = {
          success: false,
          stage: stage.name,
          output: err.stdout || '',
          error: err.message || 'Unknown error',
          duration: Date.now() - startTime
        };
        results.push(result);
        this.emitProgress(stage.name, 'failed', result);
        break;
      }
    }

    return results;
  }

  private emitProgress(stage: string, status: string, result?: PipelineResult) {
    if (this.window && !this.window.isDestroyed()) {
      this.window.webContents.send('build:progress', { stage, status, result });
    }
  }
}

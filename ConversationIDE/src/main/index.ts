import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import fs from 'fs';
import { setupChatHandlers } from './ipc/chat';
import { setupFileHandlers, setAllowedRoots } from './ipc/files';
import { setupBuildHandlers } from './ipc/build';
import { setupVANEngineHandlers } from './ipc/van_engine';
import { setupIntentForgeHandlers } from './ipc/intent_forge';
import { setupMemeForgeHandlers } from './ipc/meme_forge';
import { setupAudioHandlers } from './ipc/audio';
import { setupImageHandlers } from './ipc/image';
import { setupVideoHandlers } from './ipc/video';
import { setupPRDHandlers } from './ipc/prd';
import { setupPsychoacousticHandlers } from './ipc/psychoacoustic';
import { createWindow } from './window';

app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-software-rasterizer');

let mainWindow: BrowserWindow | null = null;

interface AppConfig {
  app: { name: string; version: string; offlineOnly: boolean };
  van_engine: { root: string; autoStart: boolean; bridges: Record<string, boolean> };
  iso: { driftThreshold: number; magnitudeTolerance: number; auditRetentionDays: number };
  ui: { theme: string; fontSize: number; voiceEnabled: boolean };
}

interface ProjectConfig {
  projects: Array<{ id: string; name: string; root: string; type: string; isWatched: boolean; iso_004_compliant: boolean }>;
}

let appConfig: AppConfig | null = null;
let projectConfig: ProjectConfig | null = null;

function loadConfigs(appRoot: string) {
  const loadJson = <T>(file: string): T | null => {
    try {
      return JSON.parse(fs.readFileSync(path.join(appRoot, 'config', file), 'utf-8'));
    } catch { return null; }
  };

  appConfig = loadJson<AppConfig>('default.json');
  const projects = loadJson<ProjectConfig>('projects.json');
  projectConfig = projects;
  const bridges = loadJson<{ bridges: any[] }>('bridges.json');

  const allowedRoots: string[] = [];
  if (projects?.projects) {
    for (const p of projects.projects) {
      allowedRoots.push(path.resolve(appRoot, p.root || '.'));
    }
  }
  if (allowedRoots.length === 0) allowedRoots.push(appRoot);
  setAllowedRoots(allowedRoots);
  console.log(`[ISO_004] Allowed roots: ${allowedRoots.join(', ')}`);
  if (appConfig) console.log(`[Config] App: ${appConfig.app.name} v${appConfig.app.version}`);
  if (bridges) console.log(`[Bridges] ${bridges.bridges.filter((b: any) => b.enabled).length} enabled`);
}

function setupConfigHandlers() {
  ipcMain.handle('config:get', async () => ({
    app: appConfig,
    projects: projectConfig?.projects || []
  }));
}

app.whenReady().then(() => {
  const appRoot = app.getAppPath();
  loadConfigs(appRoot);

  mainWindow = createWindow();

  setupConfigHandlers();
  setupChatHandlers(ipcMain, mainWindow);
  setupFileHandlers(ipcMain, mainWindow);
  setupBuildHandlers(ipcMain, mainWindow);
  setupVANEngineHandlers(ipcMain, mainWindow);
  setupIntentForgeHandlers(ipcMain, mainWindow);
  setupMemeForgeHandlers(ipcMain, mainWindow);
  setupAudioHandlers(ipcMain, mainWindow);
  setupImageHandlers(ipcMain, mainWindow);
  setupVideoHandlers(ipcMain, mainWindow);
  setupPRDHandlers(ipcMain, mainWindow);
  setupPsychoacousticHandlers(ipcMain, mainWindow);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
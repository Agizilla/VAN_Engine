const { app, BrowserWindow, ipcMain, shell, clipboard } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');

const store = new Store({
  defaults: {
    archetype: 'Chaos',
    bar_count: 8,
    spb: 16.0,
    use_glue: true,
    windowBounds: { width: 900, height: 700 }
  }
});

let mainWindow;
let pythonProcess;
let apiPort = null;

function findFreePort(start = 7860, end = 7900) {
  return new Promise((resolve) => {
    const net = require('net');
    for (let port = start; port <= end; port++) {
      const socket = new net.Socket();
      socket.once('error', () => {
        if (port === end) resolve(start);
      });
      socket.once('connect', () => {
        socket.destroy();
        resolve(port);
      });
      socket.connect(port, '127.0.0.1');
    }
  });
}

async function startPythonAPI() {
  apiPort = await findFreePort();
  console.log(`[*] Starting API on port ${apiPort}...`);
  
  pythonProcess = spawn('python', ['backend_api.py', String(apiPort)], {
    cwd: app.getAppPath(),
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false,
    shell: true
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[API] ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[API Error] ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[API] Process exited with code ${code}`);
  });

  pythonProcess.on('error', (err) => {
    console.error(`[API] Failed to start: ${err}`);
  });

  await new Promise(r => setTimeout(r, 2500));
  return apiPort;
}

function createWindow() {
  const bounds = store.get('windowBounds');
  const isDev = !app.isPackaged;
  const distPath = path.join(app.getAppPath(), 'index_2.html');
  const hasDist = fs.existsSync(distPath);
  
  const startUrl = isDev 
    ? 'http://localhost:5173' 
    : (hasDist ? `file://${distPath}` : 'about:blank');
  
  mainWindow = new BrowserWindow({
    width: bounds.width,
    height: bounds.height,
    minWidth: 700,
    minHeight: 500,
    backgroundColor: '#0a0a0a',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#1a1a1a',
      symbolColor: '#007acc',
      height: 40
    },
    icon: path.join(__dirname, 'icon.png')
  });

  mainWindow.loadURL(startUrl).catch((err) => {
    console.error(`[*] Failed to load ${startUrl}: ${err}`);
    mainWindow.loadURL('data:text/html,<html><body style="background:#0a0a0a;color:#888;font-family:monospace;"><h3>Loading...</h3><p>Check API status</p></body></html>');
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`[*] Load failed: ${errorCode} - ${errorDescription}`);
    mainWindow.loadURL('data:text/html,<html><body style="background:#0a0a0a;color:#888;font-family:monospace;"><h3>Loading...</h3><p>API may need start</p></body></html>');
  });

  mainWindow.on('resize', () => {
    const [width, height] = mainWindow.getSize();
    store.set('windowBounds', { width, height });
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(async () => {
  console.log('[*] House Codex starting...');
  
  await startPythonAPI();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.handle('get-api-port', () => apiPort);

ipcMain.handle('get-settings', () => {
  return {
    archetype: store.get('archetype'),
    bar_count: store.get('bar_count'),
    spb: store.get('spb'),
    use_glue: store.get('use_glue')
  };
});

ipcMain.handle('save-settings', (event, settings) => {
  store.set('archetype', settings.archetype);
  store.set('bar_count', settings.bar_count);
  store.set('spb', settings.spb);
  store.set('use_glue', settings.use_glue);
  return { status: 'saved' };
});

ipcMain.handle('open-folder', () => {
  shell.openPath(path.dirname(require.main.filename));
});

ipcMain.handle('copy-to-clipboard', (event, text) => {
  clipboard.writeText(text);
  return { status: 'copied' };
});
import { IpcMain, BrowserWindow } from 'electron';
import * as fs from 'fs';
import * as path from 'path';

const ALLOWED_ROOTS: string[] = [];

export function setAllowedRoots(roots: string[]) {
  ALLOWED_ROOTS.length = 0;
  ALLOWED_ROOTS.push(...roots.map(r => path.resolve(r)));
}

function isPathAllowed(targetPath: string): boolean {
  const resolved = path.resolve(targetPath);
  return ALLOWED_ROOTS.some(root => resolved.startsWith(root));
}

function getFileTree(dirPath: string, depth: number = 0, maxDepth: number = 3): any {
  if (depth > maxDepth) return null;

  const stat = fs.statSync(dirPath);
  const name = path.basename(dirPath);

  if (!stat.isDirectory()) {
    return {
      path: dirPath,
      name,
      type: 'file',
      size: stat.size,
      modified: stat.mtimeMs,
      isWatched: false
    };
  }

  const children = fs.readdirSync(dirPath)
    .filter(child => !child.startsWith('.') && child !== 'node_modules' && child !== 'dist')
    .map(child => getFileTree(path.join(dirPath, child), depth + 1, maxDepth))
    .filter(Boolean);

  return {
    path: dirPath,
    name,
    type: 'directory',
    children,
    modified: stat.mtimeMs,
    isWatched: false
  };
}

function emitAudit(window: BrowserWindow, component: string, action: string) {
  const event = { id: `audit_${Date.now()}`, timestamp: Date.now(), component, action };
  window.webContents.send('iso:audit', event);
}

export function setupFileHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('files:read', async (event, filePath: string) => {
    if (!isPathAllowed(filePath)) {
      throw new Error(`ISO_004: Access denied - path outside project root: ${filePath}`);
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    const stat = fs.statSync(filePath);
    return { content, size: stat.size, modified: stat.mtimeMs };
  });

  ipcMain.handle('files:write', async (event, filePath: string, content: string) => {
    if (!isPathAllowed(filePath)) {
      throw new Error(`ISO_004: Access denied - path outside project root: ${filePath}`);
    }
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf-8');
    emitAudit(window, 'files', `write:${filePath}`);
    return { success: true, path: filePath };
  });

  ipcMain.handle('files:tree', async (event, rootPath: string) => {
    if (!isPathAllowed(rootPath)) {
      throw new Error(`ISO_004: Access denied - path outside project root: ${rootPath}`);
    }
    return getFileTree(rootPath);
  });

  ipcMain.handle('files:delete', async (event, filePath: string) => {
    if (!isPathAllowed(filePath)) {
      throw new Error(`ISO_004: Access denied - path outside project root: ${filePath}`);
    }
    fs.unlinkSync(filePath);
    emitAudit(window, 'files', `delete:${filePath}`);
    return { success: true };
  });

  ipcMain.handle('files:mkdir', async (event, dirPath: string) => {
    if (!isPathAllowed(dirPath)) {
      throw new Error(`ISO_004: Access denied - path outside project root: ${dirPath}`);
    }
    fs.mkdirSync(dirPath, { recursive: true });
    emitAudit(window, 'files', `mkdir:${dirPath}`);
    return { success: true };
  });

  ipcMain.handle('files:exists', async (event, filePath: string) => {
    return fs.existsSync(filePath);
  });
}

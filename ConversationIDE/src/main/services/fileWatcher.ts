import * as fs from 'fs';
import * as path from 'path';
import { BrowserWindow } from 'electron';

interface WatchEntry {
  path: string;
  recursive: boolean;
  watcher: fs.FSWatcher;
}

export class FileWatcher {
  private watchers: Map<string, WatchEntry> = new Map();
  private window: BrowserWindow | null = null;

  setWindow(win: BrowserWindow) {
    this.window = win;
  }

  watch(filePath: string, recursive: boolean = false): boolean {
    if (this.watchers.has(filePath)) return false;

    try {
      const watcher = fs.watch(filePath, { recursive }, (eventType, filename) => {
        if (filename && this.window && !this.window.isDestroyed()) {
          this.window.webContents.send('files:changed', {
            path: path.join(filePath, filename),
            type: eventType,
            timestamp: Date.now()
          });
        }
      });

      this.watchers.set(filePath, { path: filePath, recursive, watcher });
      return true;
    } catch {
      return false;
    }
  }

  unwatch(filePath: string): boolean {
    const entry = this.watchers.get(filePath);
    if (entry) {
      entry.watcher.close();
      this.watchers.delete(filePath);
      return true;
    }
    return false;
  }

  unwatchAll(): void {
    for (const [, entry] of this.watchers) {
      entry.watcher.close();
    }
    this.watchers.clear();
  }

  getWatchedPaths(): string[] {
    return Array.from(this.watchers.keys());
  }
}

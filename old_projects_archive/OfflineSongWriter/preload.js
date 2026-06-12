const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAPIPort: () => ipcRenderer.invoke('get-api-port'),
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  openFolder: () => ipcRenderer.invoke('open-folder'),
  copyToClipboard: (text) => ipcRenderer.invoke('copy-to-clipboard', text),
});
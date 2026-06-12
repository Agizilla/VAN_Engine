import { contextBridge, ipcRenderer } from 'electron';

const api = {
  chat: {
    send: (message: string, conversationId: string) =>
      ipcRenderer.invoke('chat:send', { message, conversationId }),
    getHistory: (conversationId: string) =>
      ipcRenderer.invoke('chat:history', conversationId),
    getConversations: () =>
      ipcRenderer.invoke('chat:conversations'),
    onResponse: (callback: (data: any) => void) => {
      ipcRenderer.on('chat:response', (_event, data) => callback(data));
    }
  },

  files: {
    read: (filePath: string) =>
      ipcRenderer.invoke('files:read', filePath),
    write: (filePath: string, content: string) =>
      ipcRenderer.invoke('files:write', filePath, content),
    tree: (rootPath: string) =>
      ipcRenderer.invoke('files:tree', rootPath),
    delete: (filePath: string) =>
      ipcRenderer.invoke('files:delete', filePath),
    mkdir: (dirPath: string) =>
      ipcRenderer.invoke('files:mkdir', dirPath),
    exists: (filePath: string) =>
      ipcRenderer.invoke('files:exists', filePath),
    onChanged: (callback: (data: any) => void) => {
      ipcRenderer.on('files:changed', (_event, data) => callback(data));
    }
  },

  build: {
    run: (projectRoot: string, spec: string, target: string) =>
      ipcRenderer.invoke('build:run', { projectRoot, spec, target }),
    getStatus: () =>
      ipcRenderer.invoke('build:status'),
    onProgress: (callback: (data: any) => void) => {
      ipcRenderer.on('build:progress', (_event, data) => callback(data));
    }
  },

  config: {
    get: () =>
      ipcRenderer.invoke('config:get')
  },

  brain: {
    getStatus: () =>
      ipcRenderer.invoke('brain:status'),
  },

  voice: {
    synthesize: (text: string, voiceName?: string) =>
      ipcRenderer.invoke('voice:synthesize', { text, voiceName }),
    getStatus: () =>
      ipcRenderer.invoke('voice:status'),
    train: (name: string, wavPath: string, transcript: string) =>
      ipcRenderer.invoke('voice:train', { name, wavPath, transcript }),
    listVoices: () =>
      ipcRenderer.invoke('voice:list'),
  },

  algorithm: {
    execute: (query: string, effort?: string, context?: any) =>
      ipcRenderer.invoke('algorithm:execute', { query, effort, context }),
    listPRDs: () =>
      ipcRenderer.invoke('algorithm:prd:list'),
    getPRD: (slug: string) =>
      ipcRenderer.invoke('algorithm:prd:get', slug),
    updatePhase: (slug: string, phase: string) =>
      ipcRenderer.invoke('algorithm:phase:update', { slug, phase }),
    onPhaseChange: (callback: (phase: string) => void) => {
      ipcRenderer.on('algorithm:phase-change', (_event, data) => callback(data.phase));
    }
  },

  inference: {
    run: (params: { systemPrompt: string; userPrompt: string; tier: string; expectJson?: boolean }) =>
      ipcRenderer.invoke('inference:run', params),
  },

  transcript: {
    parse: (path: string) => ipcRenderer.invoke('transcript:parse', path),
  },

  skillLoader: {
    list: () => ipcRenderer.invoke('skill:list'),
    getCustomization: (skill: string) => ipcRenderer.invoke('skill:get-customization', skill),
    saveCustomization: (skill: string, content: string) =>
      ipcRenderer.invoke('skill:save-customization', skill, content),
    createCustomization: (skill: string) => ipcRenderer.invoke('skill:create-customization', skill),
  },

  vanEngine: {
    getStatus: () =>
      ipcRenderer.invoke('van-engine:status'),
    query: (query: string, context?: any) =>
      ipcRenderer.invoke('van-engine:query', query, context),
    quaternionLookup: (token: string) =>
      ipcRenderer.invoke('van-engine:quaternion:lookup', token),
    quaternionStore: (token: string, w: number, x: number, y: number, z: number, applies_to: string) =>
      ipcRenderer.invoke('van-engine:quaternion:store', token, w, x, y, z, applies_to),
    isoCheck: (ruleId: string) =>
      ipcRenderer.invoke('van-engine:iso:check', ruleId),
    isoAll: () =>
      ipcRenderer.invoke('van-engine:iso:all'),
    auditLog: (component: string, action: string) =>
      ipcRenderer.invoke('van-engine:audit:log', { component, action }),
    driftCheck: (quaternion: [number, number, number, number]) =>
      ipcRenderer.invoke('van-engine:drift:check', quaternion)
  },

  intentForge: {
    forge: (params: { intentText: string; description?: string; author?: string; autoRegister?: boolean }) =>
      ipcRenderer.invoke('intent-forge:forge', params),
    list: () =>
      ipcRenderer.invoke('intent-forge:list'),
    getCode: (skillName: string) =>
      ipcRenderer.invoke('intent-forge:get-code', skillName),
  },

  memeForge: {
    generate: (params: { topic?: string; tone?: string; frame?: string; count?: number; action?: string; meme_id?: string; tags?: string[] }) =>
      ipcRenderer.invoke('meme-forge:generate', params),
  },

  audio: {
    transcribe: (filePath: string) =>
      ipcRenderer.invoke('audio:transcribe', { filePath }),
    separateStems: (filePath: string) =>
      ipcRenderer.invoke('audio:separate-stems', { filePath }),
    synthesize: (text: string, outputPath: string) =>
      ipcRenderer.invoke('audio:synthesize', { text, outputPath }),
    classify: (filePath: string) =>
      ipcRenderer.invoke('audio:classify', { filePath }),
    modelStats: () =>
      ipcRenderer.invoke('audio:model-stats'),
    info: () =>
      ipcRenderer.invoke('audio:info'),
  },

  psychoacoustic: {
    ambient: (flavor: string, duration?: number) =>
      ipcRenderer.invoke('psychoacoustic:ambient', { flavor, duration }),
    sleepReport: () =>
      ipcRenderer.invoke('psychoacoustic:sleep-report'),
    morningReport: () =>
      ipcRenderer.invoke('psychoacoustic:morning-report'),
    detectEmotion: (sampleRate?: number) =>
      ipcRenderer.invoke('psychoacoustic:emotion', { sampleRate }),
    info: () =>
      ipcRenderer.invoke('psychoacoustic:info'),
  },

  image: {
    detect: (filePath: string) =>
      ipcRenderer.invoke('image:detect', { filePath }),
    segment: (filePath: string, points?: number[][]) =>
      ipcRenderer.invoke('image:segment', { filePath, points }),
    ocr: (filePath: string) =>
      ipcRenderer.invoke('image:ocr', { filePath }),
    info: () =>
      ipcRenderer.invoke('image:info'),
  },

  video: {
    detectFaces: (filePath: string) =>
      ipcRenderer.invoke('video:detect-faces', { filePath }),
    trim: (filePath: string, start: number, end: number, output?: string) =>
      ipcRenderer.invoke('video:trim', { filePath, start, end, output }),
    gif: (filePath: string, output?: string) =>
      ipcRenderer.invoke('video:gif', { filePath, output }),
    info: () =>
      ipcRenderer.invoke('video:info'),
  },

  prd: {
    scan: (root?: string) =>
      ipcRenderer.invoke('prd:scan', { root }),
    get: (slug: string) =>
      ipcRenderer.invoke('prd:get', { slug }),
    search: (query: string, root?: string) =>
      ipcRenderer.invoke('prd:search', { query, root }),
    getViewerPath: () =>
      ipcRenderer.invoke('prd:viewer-path'),
  }
};

ipcRenderer.on('iso:audit', (_event, data) => {
  const api = (window as any).electronAPI;
  if (api?.vanEngine?.auditLog) {
    api.vanEngine.auditLog(data.component, data.action);
  }
});

contextBridge.exposeInMainWorld('electronAPI', api);

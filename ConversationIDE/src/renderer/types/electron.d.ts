interface ChatAPI {
  send: (message: string, conversationId: string) => Promise<{
    response: string;
    intent: string;
    skill: string;
    confidence: number;
    auditId: string;
  }>;
  getHistory: (conversationId: string) => Promise<{ messages: any[]; conversationId: string }>;
  getConversations: () => Promise<{ conversations: any[] }>;
  onResponse: (callback: (data: any) => void) => void;
}

interface FilesAPI {
  read: (filePath: string) => Promise<{ content: string; size: number; modified: number }>;
  write: (filePath: string, content: string) => Promise<{ success: boolean; path: string }>;
  tree: (rootPath: string) => Promise<any>;
  delete: (filePath: string) => Promise<{ success: boolean }>;
  mkdir: (dirPath: string) => Promise<{ success: boolean }>;
  exists: (filePath: string) => Promise<boolean>;
  onChanged: (callback: (data: any) => void) => void;
}

interface BuildAPI {
  run: (projectRoot: string, spec: string, target: string) => Promise<any>;
  getStatus: () => Promise<{ available: boolean; lastBuild: any }>;
  onProgress: (callback: (data: any) => void) => void;
}

interface ConfigAPI {
  get: () => Promise<{ app: any; projects: any[] }>;
}

interface BrainStatus {
  available: boolean;
  brain?: boolean;
  diagnostics?: string;
  model?: string;
  uptime?: number;
  tokenCount?: number;
  auditCount?: number;
  activeISO?: string[];
  error?: string;
}

interface BrainAPI {
  getStatus: () => Promise<BrainStatus>;
}

interface InferenceAPI {
  run: (params: {
    systemPrompt: string;
    userPrompt: string;
    tier: 'fast' | 'standard' | 'smart';
    expectJson?: boolean;
  }) => Promise<{
    success: boolean;
    output: string;
    tier: string;
    latency_ms: number;
    error?: string;
    parsed?: any;
    from_cache?: boolean;
  }>;
}

interface TranscriptAPI {
  parse: (path: string) => Promise<{
    last_message: string;
    voice_completion: string;
    plain_completion: string;
    response_state: string;
    message_count: number;
    messages: Array<{ role: string; content: string; timestamp?: string }>;
  }>;
}

interface SkillLoaderAPI {
  list: () => Promise<Array<{ name: string; hasCustomizations: boolean; customizationPath?: string }>>;
  getCustomization: (skill: string) => Promise<{ content: string } | null>;
  saveCustomization: (skill: string, content: string) => Promise<{ success: boolean }>;
  createCustomization: (skill: string) => Promise<{ success: boolean }>;
}

interface VoiceAPI {
  notify: (data: {
    title?: string;
    message: string;
    voiceEnabled?: boolean;
    voiceId?: string;
  }) => Promise<{ played: boolean; reason?: string }>;
  getStatus: () => Promise<{ configured: boolean; defaultVoiceId: string; pronunciationRules: number }>;
}

interface DiagnosticAPI {
  apiTest: () => Promise<any[]>;
}

interface VanEngineAPI {
  getStatus: () => Promise<{ available: boolean; path: string; isoCount: number }>;
  quaternionLookup: (token: string) => Promise<{ w: number; x: number; y: number; z: number } | null>;
  quaternionStore: (token: string, w: number, x: number, y: number, z: number, applies_to: string) => Promise<{ stored: boolean; error?: string }>;
  isoCheck: (ruleId: string) => Promise<{ ruleId: string; status: string; name: string; timestamp: number }>;
  isoAll: () => Promise<{ rules: any[] }>;
  auditLog: (component: string, action: string) => Promise<{ logged: boolean; id: string }>;
  driftCheck: (quaternion: [number, number, number, number]) => Promise<{ violated: boolean; action: string }>;
}

interface AlgorithmAPI {
  execute: (query: string, effort?: string, context?: any) => Promise<{
    success: boolean;
    effort: string;
    timeUsedSeconds: number;
    timeBudgetSeconds: number;
    phases: Record<string, any>;
  }>;
  listPRDs: () => Promise<{
    prds: Array<{
      slug: string;
      task: string;
      phase: string;
      progress: string;
      updated: number;
    }>;
  }>;
  getPRD: (slug: string) => Promise<{
    content: string;
    slug: string;
  }>;
  updatePhase: (slug: string, phase: string) => Promise<{ success: boolean }>;
  onPhaseChange: (callback: (phase: string) => void) => void;
}

interface MemeForgeAPI {
  generate: (params: {
    topic?: string; tone?: string; frame?: string; count?: number;
    action?: string; meme_id?: string; tags?: string[];
  }) => Promise<{ error: string | null; result: any }>;
}

interface PRDAPI {
  scan: (root?: string) => Promise<{ error?: string; prds?: any[]; catalog?: any }>;
  get: (slug: string) => Promise<{ error?: string; prd?: any }>;
  search: (query: string, root?: string) => Promise<{ error?: string; results?: any[]; count?: number }>;
  getViewerPath: () => Promise<{ path: string; exists: boolean }>;
}

interface AudioAPI {
  transcribe: (filePath: string) => Promise<{ error: string | null; result: any }>;
  separateStems: (filePath: string) => Promise<{ error: string | null; result: any }>;
  synthesize: (text: string, outputPath: string) => Promise<{ error: string | null; result: any }>;
  classify: (filePath: string) => Promise<{ error: string | null; result: any }>;
  modelStats: () => Promise<{ error: string | null; result: any }>;
  info: () => Promise<{ error: string | null; result: { meta: any; capabilities: string[] } }>;
}

interface PsychoacousticAPI {
  ambient: (flavor: string, duration?: number) => Promise<{ error: string | null; result: any }>;
  sleepReport: () => Promise<{ error: string | null; result: any }>;
  morningReport: () => Promise<{ error: string | null; result: any }>;
  detectEmotion: (sampleRate?: number) => Promise<{ error: string | null; result: any }>;
  info: () => Promise<{ error: string | null; result: { meta: any; capabilities: string[] } }>;
}

interface ImageAPI {
  detect: (filePath: string) => Promise<{ error: string | null; result: any }>;
  segment: (filePath: string, points?: number[][]) => Promise<{ error: string | null; result: any }>;
  ocr: (filePath: string) => Promise<{ error: string | null; result: any }>;
  info: () => Promise<{ error: string | null; result: { meta: any; capabilities: string[] } }>;
}

interface VideoAPI {
  detectFaces: (filePath: string) => Promise<{ error: string | null; result: any }>;
  trim: (filePath: string, start: number, end: number, output?: string) => Promise<{ error: string | null; result: any }>;
  gif: (filePath: string, output?: string) => Promise<{ error: string | null; result: any }>;
  info: () => Promise<{ error: string | null; result: { meta: any; capabilities: string[] } }>;
}

interface IntentForgeAPI {
  forge: (params: {
    intentText: string;
    description?: string;
    author?: string;
    autoRegister?: boolean;
  }) => Promise<{
    error: string | null;
    result: {
      skill_name: string;
      file_path: string;
      class_name: string;
      intent_summary: string;
      grid_label: string;
      registered: boolean;
      code?: string;
    } | null;
  }>;
  list: () => Promise<{
    skills: Array<{
      name: string;
      path: string;
      size: number;
      modified: string;
    }>;
  }>;
  getCode: (skillName: string) => Promise<{
    error: string | null;
    content: string | null;
  }>;
}

interface ElectronAPI {
  config: ConfigAPI;
  diagnostic: DiagnosticAPI;
  chat: ChatAPI;
  files: FilesAPI;
  build: BuildAPI;
  brain: BrainAPI;
  voice: VoiceAPI;
  algorithm: AlgorithmAPI;
  vanEngine: VanEngineAPI;
  inference: InferenceAPI;
  transcript: TranscriptAPI;
  skillLoader: SkillLoaderAPI;
  intentForge: IntentForgeAPI;
  memeForge: MemeForgeAPI;
  audio: AudioAPI;
  psychoacoustic: PsychoacousticAPI;
  image: ImageAPI;
  video: VideoAPI;
  prd: PRDAPI;
}

interface Window {
  electronAPI: ElectronAPI;
}

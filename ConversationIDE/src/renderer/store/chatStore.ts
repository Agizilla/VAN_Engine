import { create } from 'zustand';

export type MessageIntent = 'task' | 'question' | 'command' | 'conversation';
export type EffortEstimate = 'standard' | 'extended' | 'advanced' | 'deep' | 'comprehensive';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  metadata?: {
    intent?: MessageIntent;
    effort?: EffortEstimate;
    skill?: string;
    confidence?: number;
    iso_violation?: boolean;
    audit_id?: string;
  };
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  created: number;
  modified: number;
  project_root?: string;
}

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isConnected: boolean;
  apiState: 'idle' | 'starting' | 'ready' | 'error';
  apiDetail: string;
  isLoading: boolean;

  brainReady: boolean;
  brainUptime: number;
  brainTokenCount: number;
  brainAuditCount: number;
  brainActiveISO: string[];

  addMessage: (message: Omit<ChatMessage, 'id'>) => void;
  sendMessage: (content: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  loadHistory: (conversationId: string) => Promise<void>;
  setCurrentConversation: (id: string) => void;
  createConversation: (title?: string) => void;
  setConnected: (connected: boolean) => void;
  setApiState: (state: ChatState['apiState'], detail?: string) => void;
  setLoading: (loading: boolean) => void;
  pollBrainStatus: () => Promise<void>;
}

let messageCounter = 0;

function classifyIntent(content: string): MessageIntent {
  const lower = content.toLowerCase().trim();

  const taskKeywords = [
    'build', 'implement', 'create', 'add', 'fix', 'refactor', 'update',
    'change', 'write', 'make', 'develop', 'configure', 'setup',
    'migrate', 'integrate', 'deploy', 'optimize', 'rewrite',
  ];
  const commandKeywords = [
    'run', 'execute', 'start', 'stop', 'launch', 'deploy', 'restart',
    'test', 'compile', 'build ', 'install', 'publish',
  ];

  if (lower.includes('?') && lower.length < 200) return 'question';
  if (taskKeywords.some((kw) => lower.includes(kw))) return 'task';
  if (commandKeywords.some((kw) => lower.startsWith(kw) || lower.includes(` ${kw}`))) return 'command';
  if (lower.length > 100) return 'task';

  return 'conversation';
}

function estimateEffort(content: string): EffortEstimate {
  const len = content.length;
  const taskIndicators = (content.match(/implement|build|create|refactor|migrate|integrate/gi) || []).length;

  if (len > 500 || taskIndicators > 3) return 'comprehensive';
  if (len > 300 || taskIndicators > 2) return 'deep';
  if (len > 150 || taskIndicators > 1) return 'advanced';
  if (len > 80 || taskIndicators > 0) return 'extended';
  return 'standard';
}

function getAPI() {
  return (window as any).electronAPI;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  isConnected: false,
  apiState: 'idle',
  apiDetail: '',
  isLoading: false,

  brainReady: false,
  brainUptime: 0,
  brainTokenCount: 0,
  brainAuditCount: 0,
  brainActiveISO: [],

  addMessage: (message) => {
    const msg: ChatMessage = {
      ...message,
      id: `msg_${Date.now()}_${messageCounter++}`
    };

    set((state) => {
      const conv = state.currentConversation;
      if (!conv) {
        const newConv: Conversation = {
          id: `conv_${Date.now()}`,
          title: message.content.slice(0, 50),
          messages: [msg],
          created: Date.now(),
          modified: Date.now()
        };
        return {
          conversations: [...state.conversations, newConv],
          currentConversation: newConv
        };
      }

      const updatedConv = {
        ...conv,
        messages: [...conv.messages, msg],
        modified: Date.now()
      };

      return {
        currentConversation: updatedConv,
        conversations: state.conversations.map(c =>
          c.id === conv.id ? updatedConv : c
        )
      };
    });
  },

  sendMessage: async (content: string) => {
    const api = getAPI();

    const intent = classifyIntent(content);
    const effort = estimateEffort(content);

    get().addMessage({
      role: 'user', content, timestamp: Date.now(),
      metadata: { intent, effort },
    });

    set({ apiState: 'starting', apiDetail: '' });

    let reply: string | null = null;
    const responseMetadata: ChatMessage['metadata'] = {
      intent,
      effort,
      skill: 'general',
      confidence: intent === 'conversation' ? 0.8 : 0.65,
    };

    if (api?.chat?.send) {
      try {
        const response = await api.chat.send(content, '');
        reply = response?.response || null;
        if (reply) {
          set({ apiState: 'ready', apiDetail: 'Brain online' });
        }
      } catch { }
    }

    if (reply) {
      set({ isConnected: true });
      get().addMessage({
        role: 'assistant',
        content: reply,
        timestamp: Date.now(),
        metadata: responseMetadata,
      });
    } else {
      set({ isConnected: false, apiState: 'error', apiDetail: 'Unable to reach local API' });
      get().addMessage({
        role: 'assistant',
        content: `⚠️ Cannot reach VAN_Engine API at http://127.0.0.1:44444.\nThe app should auto-start it from api/server.py.`,
        timestamp: Date.now(),
        metadata: { intent: 'conversation', effort: 'standard' },
      });
    }
  },

  loadConversations: async () => {
    const api = getAPI();
    if (api?.chat?.getConversations) {
      try {
        const { conversations } = await api.chat.getConversations();
        if (conversations) {
          set({ conversations, isConnected: true, apiState: 'ready', apiDetail: 'Brain ready' });
        }
    } catch { }
    }
  },

  loadHistory: async (conversationId: string) => {
    const api = getAPI();
    if (api?.chat?.getHistory) {
      try {
        const { messages } = await api.chat.getHistory(conversationId);
        if (messages) {
          set((state) => {
            const updatedConv = {
              ...state.currentConversation,
              messages,
              modified: Date.now()
            } as Conversation;
            return {
              currentConversation: updatedConv,
              conversations: state.conversations.map(c =>
                c.id === conversationId ? updatedConv : c
              )
            };
          });
        }
      } catch { }
    }
  },

  setCurrentConversation: (id) => {
    const conv = get().conversations.find(c => c.id === id);
    if (conv) {
      set({ currentConversation: conv });
      get().loadHistory(id);
    }
  },

  createConversation: (title) => {
    const conv: Conversation = {
      id: `conv_${Date.now()}`,
      title: title || 'New Conversation',
      messages: [],
      created: Date.now(),
      modified: Date.now()
    };
    set((state) => ({
      conversations: [...state.conversations, conv],
      currentConversation: conv
    }));
  },

  setConnected: (connected) => set({ isConnected: connected }),
  setApiState: (state, detail = '') => set({ apiState: state, apiDetail: detail }),
  setLoading: (loading) => set({ isLoading: loading }),

  pollBrainStatus: async () => {
    const api = getAPI();
    if (!api?.brain?.getStatus) return;
    try {
      const status = await api.brain.getStatus();
      if (status.available) {
        set({
          apiState: 'ready',
          apiDetail: status.diagnostics || 'Brain online',
          isConnected: true,
          brainReady: status.brain ?? false,
          brainUptime: status.uptime ?? 0,
          brainTokenCount: status.tokenCount ?? 0,
          brainAuditCount: status.auditCount ?? 0,
          brainActiveISO: status.activeISO ?? [],
        });
      } else {
        set({ apiState: 'error', apiDetail: status.error || 'Brain unavailable' });
      }
    } catch {
      set({ apiState: 'error', apiDetail: 'Failed to poll brain status' });
    }
  }
}));

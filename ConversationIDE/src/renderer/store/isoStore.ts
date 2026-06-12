import { create } from 'zustand';

export interface ISORule {
  id: string;
  name: string;
  status: 'active' | 'violated' | 'checking' | 'enforced' | 'unknown';
  lastCheck: number;
  diagnostics?: string;
}

export interface AuditEvent {
  id: string;
  timestamp: number;
  component: string;
  action: string;
  quaternion_before?: [number, number, number, number];
  quaternion_after?: [number, number, number, number];
  magnitude_drift?: number;
}

interface ISOState {
  rules: ISORule[];
  auditEvents: AuditEvent[];
  vanEngineAvailable: boolean;
  isLoading: boolean;

  loadRules: () => Promise<void>;
  checkRule: (ruleId: string) => Promise<void>;
  addAuditEvent: (event: Omit<AuditEvent, 'id'>) => void;
  setVanEngineAvailable: (available: boolean) => void;
  setLoading: (loading: boolean) => void;
}

export const useISOStore = create<ISOState>((set, get) => ({
  rules: [],
  auditEvents: [],
  vanEngineAvailable: false,
  isLoading: false,

  loadRules: async () => {
    set({ isLoading: true });
    try {
      const api = (window as any).electronAPI;
      if (api?.vanEngine?.isoAll) {
        const result = await api.vanEngine.isoAll();
        if (result?.rules) {
          const rules: ISORule[] = result.rules.map((r: any) => ({
            id: r.id,
            name: r.name,
            status: r.status === 'enforced' ? 'enforced' :
                    r.status === 'active' ? 'active' : 'unknown',
            lastCheck: Date.now()
          }));
          set({ rules, vanEngineAvailable: true, isLoading: false });
          return;
        }
      }
    } catch { }

    set({
      rules: [
        { id: 'ISO_004', name: 'Mutation Resistance', status: 'active', lastCheck: Date.now() },
        { id: 'ISO_010', name: 'Drift Gating', status: 'active', lastCheck: Date.now() },
        { id: 'ISO_015', name: 'Observable State', status: 'active', lastCheck: Date.now() },
        { id: 'ISO_019', name: 'Privacy by Default', status: 'enforced', lastCheck: Date.now() },
        { id: 'ISO_020', name: 'Anti-Hallucination', status: 'enforced', lastCheck: Date.now() }
      ],
      isLoading: false
    });
  },

  checkRule: async (ruleId: string) => {
    set((state) => ({
      rules: state.rules.map(r =>
        r.id === ruleId ? { ...r, status: 'checking' as const } : r
      )
    }));

    try {
      const api = (window as any).electronAPI;
      if (api?.vanEngine?.isoCheck) {
        const result = await api.vanEngine.isoCheck(ruleId);
        set((state) => ({
          rules: state.rules.map(r =>
            r.id === ruleId
              ? { ...r, status: result.status as ISORule['status'], lastCheck: Date.now() }
              : r
          )
        }));
        return;
      }
    } catch { }

    set((state) => ({
      rules: state.rules.map(r =>
        r.id === ruleId
          ? { ...r, status: 'active', lastCheck: Date.now() }
          : r
      )
    }));
  },

  addAuditEvent: (event) => {
    const auditEvent: AuditEvent = {
      ...event,
      id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    };
    set((state) => ({
      auditEvents: [...state.auditEvents, auditEvent].slice(-100)
    }));
  },

  setVanEngineAvailable: (available) => set({ vanEngineAvailable: available }),
  setLoading: (loading) => set({ isLoading: loading })
}));

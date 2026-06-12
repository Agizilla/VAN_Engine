import { create } from 'zustand';

export type AlgorithmPhase =
  | 'observe'
  | 'think'
  | 'plan'
  | 'build'
  | 'execute'
  | 'verify'
  | 'learn'
  | 'complete';

export type EffortLevel =
  | 'standard'
  | 'extended'
  | 'advanced'
  | 'deep'
  | 'comprehensive';

export interface ISCCriterion {
  id: string;
  label: string;
  done: boolean;
  evidence: string;
  createdAt: number;
}

interface PhaseState {
  currentPhase: AlgorithmPhase;
  effortLevel: EffortLevel;
  timeBudgetMs: number;
  timeElapsedMs: number;
  autoCompress: boolean;
  criteria: ISCCriterion[];
  voiceEnabled: boolean;
  history: { phase: AlgorithmPhase; enteredAt: number }[];

  setPhase: (phase: AlgorithmPhase, announce?: boolean) => void;
  setEffortLevel: (level: EffortLevel) => void;
  setTimeBudget: (ms: number) => void;
  tickElapsed: (ms: number) => void;
  setAutoCompress: (v: boolean) => void;
  addCriterion: (label: string) => void;
  toggleCriterion: (id: string) => void;
  setCriterionEvidence: (id: string, evidence: string) => void;
  removeCriterion: (id: string) => void;
  clearCriteria: () => void;
  setVoiceEnabled: (v: boolean) => void;
  reset: () => void;
}

const PHASE_LABELS: Record<AlgorithmPhase, string> = {
  observe: 'Observe',
  think: 'Think',
  plan: 'Plan',
  build: 'Build',
  execute: 'Execute',
  verify: 'Verify',
  learn: 'Learn',
  complete: 'Complete',
};

export function formatPhaseLabel(phase: AlgorithmPhase): string {
  return PHASE_LABELS[phase];
}

export const PHASE_ORDER: AlgorithmPhase[] = [
  'observe', 'think', 'plan', 'build', 'execute', 'verify', 'learn', 'complete',
];

const EFFORT_BUDGETS: Record<EffortLevel, number> = {
  standard: 120_000,
  extended: 480_000,
  advanced: 960_000,
  deep: 1_920_000,
  comprehensive: 7_200_000,
};

export function getEffortBudget(level: EffortLevel): number {
  return EFFORT_BUDGETS[level];
}

function loadPersistedState(): Partial<PhaseState> {
  try {
    const raw = localStorage.getItem('cide_phase_state');
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return {
      currentPhase: parsed.currentPhase || 'observe',
      effortLevel: parsed.effortLevel || 'standard',
      criteria: parsed.criteria || [],
      voiceEnabled: parsed.voiceEnabled ?? true,
      timeBudgetMs: parsed.timeBudgetMs || EFFORT_BUDGETS.standard,
      history: parsed.history || [{ phase: 'observe', enteredAt: Date.now() }],
    };
  } catch {
    return {};
  }
}

function persistState(state: PhaseState) {
  try {
    localStorage.setItem('cide_phase_state', JSON.stringify({
      currentPhase: state.currentPhase,
      effortLevel: state.effortLevel,
      criteria: state.criteria,
      voiceEnabled: state.voiceEnabled,
      timeBudgetMs: state.timeBudgetMs,
      history: state.history.slice(-20),
    }));
  } catch { }
}

let criteriaCounter = 0;

export const usePhaseStore = create<PhaseState>((set, get) => {
  const persisted = loadPersistedState();

  return {
    currentPhase: persisted.currentPhase || 'observe',
    effortLevel: persisted.effortLevel || 'standard',
    timeBudgetMs: persisted.timeBudgetMs || EFFORT_BUDGETS.standard,
    timeElapsedMs: 0,
    autoCompress: false,
    criteria: persisted.criteria || [],
    voiceEnabled: persisted.voiceEnabled ?? true,
    history: persisted.history || [{ phase: 'observe', enteredAt: Date.now() }],

    setPhase: (phase, announce = true) => {
      set((state) => {
        const newHistory = [...state.history, { phase, enteredAt: Date.now() }];
        const next = {
          currentPhase: phase,
          history: newHistory.slice(-20),
          autoCompress: false,
        };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
      if (window.electronAPI?.algorithm) {
        window.electronAPI.algorithm.updatePhase('current', phase).catch(() => {});
      }
    },

    setEffortLevel: (level) => {
      set((state) => {
        const budget = EFFORT_BUDGETS[level];
        const next = { effortLevel: level, timeBudgetMs: budget };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    setTimeBudget: (ms) => set({ timeBudgetMs: ms }),
    tickElapsed: (ms) => set((state) => ({ timeElapsedMs: state.timeElapsedMs + ms })),

    setAutoCompress: (v) => set({ autoCompress: v }),

    addCriterion: (label) => {
      set((state) => {
        const criterion: ISCCriterion = {
          id: `isc_${++criteriaCounter}`,
          label,
          done: false,
          evidence: '',
          createdAt: Date.now(),
        };
        const next = { criteria: [...state.criteria, criterion] };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    toggleCriterion: (id) => {
      set((state) => {
        const next = {
          criteria: state.criteria.map((c) =>
            c.id === id ? { ...c, done: !c.done } : c
          ),
        };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    setCriterionEvidence: (id, evidence) => {
      set((state) => {
        const next = {
          criteria: state.criteria.map((c) =>
            c.id === id ? { ...c, evidence } : c
          ),
        };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    removeCriterion: (id) => {
      set((state) => {
        const next = { criteria: state.criteria.filter((c) => c.id !== id) };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    clearCriteria: () => {
      set((state) => {
        const next = { criteria: [] };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    setVoiceEnabled: (v) => {
      set((state) => {
        const next = { voiceEnabled: v };
        persistState({ ...state, ...next } as PhaseState);
        return next;
      });
    },

    reset: () => {
      const next = {
        currentPhase: 'observe' as AlgorithmPhase,
        effortLevel: 'standard' as EffortLevel,
        timeBudgetMs: EFFORT_BUDGETS.standard,
        timeElapsedMs: 0,
        autoCompress: false,
        criteria: [],
        history: [{ phase: 'observe' as AlgorithmPhase, enteredAt: Date.now() }],
      };
      persistState({ ...next } as PhaseState);
      set(next);
    },
  };
});

let _phaseListenerInitialized = false;

export function initPhaseListener() {
  if (_phaseListenerInitialized) return;
  _phaseListenerInitialized = true;
  if (window.electronAPI?.algorithm?.onPhaseChange) {
    window.electronAPI.algorithm.onPhaseChange((phase: string) => {
      const state = usePhaseStore.getState();
      if (state.currentPhase !== phase) {
        state.setPhase(phase as AlgorithmPhase, false);
      }
    });
  }
}

import React, { useState, useEffect } from 'react';

interface PRD {
  slug: string;
  task: string;
  phase: string;
  progress: string;
  updated: number;
}

export const AlgorithmPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [effort, setEffort] = useState<string>('standard');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [prds, setPRDs] = useState<PRD[]>([]);
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);

  useEffect(() => {
    loadPRDs();
    if (window.electronAPI.algorithm.onPhaseChange) {
      window.electronAPI.algorithm.onPhaseChange((phase) => {
        setCurrentPhase(phase);
      });
    }
  }, []);

  const loadPRDs = async () => {
    try {
      const response = await window.electronAPI.algorithm.listPRDs();
      setPRDs(response.prds);
    } catch (error) {
      console.error('Failed to load PRDs:', error);
    }
  };

  const handleExecute = async () => {
    if (!query.trim()) return;

    setIsRunning(true);
    setCurrentPhase(null);
    setResult(null);

    try {
      const response = await window.electronAPI.algorithm.execute(query, effort);
      setResult(response);
      await loadPRDs();
    } catch (error: any) {
      setResult({ success: false, error: error.message });
    } finally {
      setIsRunning(false);
    }
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs.toFixed(0)}s`;
  };

  return (
    <div className="algorithm-panel">
      <h2>PAI Algorithm v3.7.0</h2>
      <p className="subtitle">Observe → Think → Plan → Build → Execute → Verify → Learn</p>

      <div className="query-section">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe your task... The Algorithm will decompose it into verifiable ISC criteria."
          rows={4}
        />

        <div className="effort-selector">
          <label>Effort Tier:</label>
          <select value={effort} onChange={(e) => setEffort(e.target.value)}>
            <option value="standard">Standard (&lt;2min, 8+ ISC)</option>
            <option value="extended">Extended (&lt;8min, 16+ ISC)</option>
            <option value="advanced">Advanced (&lt;16min, 24+ ISC)</option>
            <option value="deep">Deep (&lt;32min, 40+ ISC)</option>
            <option value="comprehensive">Comprehensive (&lt;120min, 64+ ISC)</option>
          </select>
          <button onClick={handleExecute} disabled={isRunning || !query.trim()}>
            {isRunning ? 'Running Algorithm...' : 'Execute Algorithm'}
          </button>
        </div>
      </div>

      {currentPhase && (
        <div className="phase-indicator">
          <span className="phase-label">Current Phase:</span>
          <span className="phase-value">{currentPhase.toUpperCase()}</span>
          <div className="phase-steps">
            {['Observe', 'Think', 'Plan', 'Build', 'Execute', 'Verify', 'Learn'].map((p) => (
              <React.Fragment key={p}>
                <span className={currentPhase.toLowerCase() === p.toLowerCase() ? 'active' : ''}>
                  {p}
                </span>
                {p !== 'Learn' && <span className="arrow">→</span>}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className={`result-section ${result.success ? 'success' : 'error'}`}>
          <h3>{result.success ? 'Algorithm Complete' : 'Algorithm Failed'}</h3>
          <div className="result-metrics">
            <div className="metric">
              <span className="metric-label">Effort:</span>
              <span className="metric-value">{result.effort}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Time:</span>
              <span className="metric-value">{formatTime(result.timeUsedSeconds)} / {formatTime(result.timeBudgetSeconds)}</span>
            </div>
          </div>
          {result.error && <div className="result-message">{result.error}</div>}
        </div>
      )}

      <div className="prd-list">
        <h3>Recent PRDs</h3>
        <div className="prd-items">
          {prds.length === 0 && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No PRDs yet</div>}
          {prds.map((prd) => (
            <div key={prd.slug} className="prd-item">
              <div className="prd-task">{prd.task}</div>
              <div className="prd-meta">
                <span className={`prd-phase phase-${prd.phase}`}>{prd.phase}</span>
                <span className="prd-progress">{prd.progress}</span>
                <span className="prd-date">{new Date(prd.updated).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .algorithm-panel {
          padding: 1.5rem;
          background: var(--bg-primary);
          color: var(--text-primary);
          overflow-y: auto;
          height: 100%;
        }
        .algorithm-panel h2 {
          color: var(--accent-cyan);
          margin-bottom: 0.25rem;
          font-size: 1.1rem;
        }
        .subtitle {
          color: var(--text-muted);
          font-size: 0.8rem;
          margin-bottom: 1.5rem;
        }
        .query-section {
          margin-bottom: 1.5rem;
        }
        textarea {
          width: 100%;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0.75rem;
          color: var(--text-primary);
          font-family: inherit;
          font-size: 0.85rem;
          resize: vertical;
        }
        textarea:focus {
          outline: none;
          border-color: var(--accent-cyan);
        }
        .effort-selector {
          display: flex;
          gap: 0.75rem;
          margin-top: 0.75rem;
          align-items: center;
          flex-wrap: wrap;
        }
        .effort-selector label {
          font-size: 0.8rem;
          color: var(--text-muted);
        }
        select, button {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 0.4rem 0.75rem;
          color: var(--text-primary);
          font-size: 0.8rem;
          cursor: pointer;
        }
        .effort-selector button {
          background: var(--accent-cyan);
          color: #000;
          font-weight: 600;
        }
        .effort-selector button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .phase-indicator {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0.75rem;
          margin-bottom: 1rem;
        }
        .phase-label {
          font-size: 0.7rem;
          text-transform: uppercase;
          color: var(--text-muted);
          letter-spacing: 0.05em;
        }
        .phase-value {
          font-size: 1.1rem;
          font-weight: bold;
          color: var(--accent-cyan);
          margin-left: 0.5rem;
        }
        .phase-steps {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 0.25rem;
          margin-top: 0.5rem;
        }
        .phase-steps span {
          font-size: 0.7rem;
          padding: 0.2rem 0.4rem;
          border-radius: 4px;
          background: var(--bg-primary);
          color: var(--text-muted);
        }
        .phase-steps .active {
          background: var(--accent-cyan);
          color: #000;
          font-weight: 600;
        }
        .arrow {
          background: transparent !important;
          color: var(--text-muted) !important;
          padding: 0 0.15rem !important;
        }
        .result-section {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 1rem;
          margin-bottom: 1rem;
        }
        .result-section.success {
          border-left: 4px solid var(--success);
        }
        .result-section.error {
          border-left: 4px solid var(--error);
        }
        .result-section h3 {
          font-size: 0.95rem;
          margin-bottom: 0.5rem;
        }
        .result-metrics {
          display: flex;
          gap: 1rem;
          margin: 0.5rem 0;
        }
        .metric {
          background: var(--bg-primary);
          padding: 0.4rem 0.75rem;
          border-radius: 6px;
          font-size: 0.8rem;
        }
        .metric-label {
          color: var(--text-muted);
          margin-right: 0.4rem;
        }
        .metric-value {
          font-weight: 600;
        }
        .result-message {
          color: var(--error);
          font-size: 0.8rem;
          margin-top: 0.5rem;
        }
        .prd-list h3 {
          font-size: 0.9rem;
          color: var(--accent-cyan);
          margin-bottom: 0.75rem;
        }
        .prd-item {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 0.6rem 0.75rem;
          margin-bottom: 0.4rem;
        }
        .prd-task {
          font-size: 0.8rem;
          font-weight: 500;
          margin-bottom: 0.25rem;
        }
        .prd-meta {
          display: flex;
          gap: 0.75rem;
          font-size: 0.65rem;
          color: var(--text-muted);
        }
        .prd-phase {
          padding: 0.1rem 0.35rem;
          border-radius: 4px;
        }
        .prd-progress {
          font-family: monospace;
        }
        .phase-observe { background: rgba(96,165,250,0.2); color: #60a5fa; }
        .phase-think { background: rgba(167,139,250,0.2); color: #a78bfa; }
        .phase-plan { background: rgba(251,191,36,0.2); color: #fbbf24; }
        .phase-build { background: rgba(248,113,113,0.2); color: #f87171; }
        .phase-execute { background: rgba(74,222,128,0.2); color: #4ade80; }
        .phase-verify { background: rgba(34,211,238,0.2); color: #22d3ee; }
        .phase-learn { background: rgba(244,114,182,0.2); color: #f472b6; }
      `}</style>
    </div>
  );
};

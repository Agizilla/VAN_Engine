import React, { useState } from 'react';
import { useInference, InferenceTier } from '../../hooks/useInference';

export const InferencePanel: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [selectedTier, setSelectedTier] = useState<InferenceTier>('standard');
  const { isLoading, result, error, runInference, clearResult } = useInference();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    await runInference(prompt, selectedTier);
  };

  const handleClear = () => {
    setPrompt('');
    clearResult();
  };

  const getTierColor = (tier: InferenceTier) => {
    switch (tier) {
      case 'fast': return 'var(--success)';
      case 'standard': return 'var(--accent-cyan)';
      case 'smart': return 'var(--accent-gold)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div className="inference-panel">
      <h2>Inference Engine</h2>
      <p className="subtitle">Fast / Standard / Smart — Pick the right tier</p>

      <div className="tier-selector">
        <button className={`tier-btn ${selectedTier === 'fast' ? 'active' : ''}`}
          onClick={() => setSelectedTier('fast')}>
          Fast<span className="tier-desc">Pattern matching</span>
        </button>
        <button className={`tier-btn ${selectedTier === 'standard' ? 'active' : ''}`}
          onClick={() => setSelectedTier('standard')}>
          Standard<span className="tier-desc">Brain query</span>
        </button>
        <button className={`tier-btn ${selectedTier === 'smart' ? 'active' : ''}`}
          onClick={() => setSelectedTier('smart')}>
          Smart<span className="tier-desc">7-phase Algorithm</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="inference-form">
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt..." rows={4} disabled={isLoading} />
        <div className="form-actions">
          <button type="submit" disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Processing...' : 'Run Inference'}
          </button>
          <button type="button" onClick={handleClear} disabled={isLoading}>Clear</button>
        </div>
      </form>

      {isLoading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <span>Running {selectedTier} inference...</span>
        </div>
      )}

      {result && (
        <div className="result-container">
          <div className="result-header">
            <span className="result-tier" style={{ color: getTierColor(result.tier) }}>
              {result.tier.toUpperCase()}
            </span>
            {result.fromCache && <span className="cache-badge">Cached</span>}
            <span className="result-latency">{result.latencyMs.toFixed(0)}ms</span>
          </div>
          <div className="result-output"><pre>{result.output}</pre></div>
          {result.parsed && (
            <details className="result-details">
              <summary>Metadata</summary>
              <pre>{JSON.stringify(result.parsed, null, 2)}</pre>
            </details>
          )}
        </div>
      )}

      {error && <div className="error-container"><span>{error}</span></div>}
    </div>
  );
};

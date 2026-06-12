import React, { useState } from 'react';
import { usePhaseStore, formatPhaseLabel } from '../../store/phaseStore';

export const CriteriaPanel: React.FC = () => {
  const {
    currentPhase, criteria, effortLevel, timeBudgetMs, timeElapsedMs,
    addCriterion, toggleCriterion, setCriterionEvidence, removeCriterion, clearCriteria,
  } = usePhaseStore();

  const [newLabel, setNewLabel] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const doneCount = criteria.filter((c) => c.done).length;
  const totalCount = criteria.length;
  const progressPct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  const budgetRemaining = Math.max(0, timeBudgetMs - timeElapsedMs);
  const budgetPct = timeBudgetMs > 0 ? Math.min(100, Math.round((timeElapsedMs / timeBudgetMs) * 100)) : 0;

  const handleAdd = () => {
    const trimmed = newLabel.trim();
    if (!trimmed) return;
    addCriterion(trimmed);
    setNewLabel('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="criteria-panel">
      <div className="criteria-header">
        <h3>Criteria</h3>
        <div className="criteria-phase-badge">{formatPhaseLabel(currentPhase)}</div>
      </div>

      <div className="criteria-meta">
        <span className={`criteria-effort effort-${effortLevel}`}>{effortLevel}</span>
        <span className="criteria-progress">{doneCount}/{totalCount} ({progressPct}%)</span>
      </div>

      <div className="criteria-budget-bar">
        <div
          className={`criteria-budget-fill ${budgetPct > 80 ? 'over' : budgetPct > 50 ? 'warn' : ''}`}
          style={{ width: `${budgetPct}%` }}
        />
        <span className="criteria-budget-label">{Math.round(budgetRemaining / 1000)}s left</span>
      </div>

      <div className="criteria-add-row">
        <input
          type="text"
          value={newLabel}
          onChange={(e) => setNewLabel(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add criterion..."
          className="criteria-input"
        />
        <button onClick={handleAdd} disabled={!newLabel.trim()} className="criteria-add-btn">+</button>
      </div>

      <div className="criteria-list">
        {criteria.length === 0 && (
          <div className="criteria-empty">No criteria yet. Add task checkboxes above.</div>
        )}
        {criteria.map((c) => (
          <div key={c.id} className={`criteria-item ${c.done ? 'done' : ''}`}>
            <input
              type="checkbox"
              checked={c.done}
              onChange={() => toggleCriterion(c.id)}
              className="criteria-checkbox"
            />
            <div className="criteria-content">
              <span
                className="criteria-label"
                onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}
              >
                {c.label}
              </span>
              {expandedId === c.id && (
                <div className="criteria-detail">
                  <input
                    type="text"
                    value={c.evidence}
                    onChange={(e) => setCriterionEvidence(c.id, e.target.value)}
                    placeholder="Verification evidence..."
                    className="criteria-evidence-input"
                  />
                </div>
              )}
            </div>
            <button
              onClick={() => removeCriterion(c.id)}
              className="criteria-remove-btn"
              title="Remove criterion"
            >×</button>
          </div>
        ))}
      </div>

      {totalCount > 0 && (
        <button onClick={clearCriteria} className="criteria-clear-btn">Clear All</button>
      )}
    </div>
  );
};

import React from 'react';
import { usePhaseStore, AlgorithmPhase, PHASE_ORDER, formatPhaseLabel, EffortLevel } from '../../store/phaseStore';
import { speak } from '../../hooks/useVoiceCommands';

const EFFORT_LEVELS: { value: EffortLevel; label: string }[] = [
  { value: 'standard', label: 'Std' },
  { value: 'extended', label: 'Ext' },
  { value: 'advanced', label: 'Adv' },
  { value: 'deep', label: 'Deep' },
  { value: 'comprehensive', label: 'Comp' },
];

function getNextPhase(current: AlgorithmPhase): AlgorithmPhase | null {
  const idx = PHASE_ORDER.indexOf(current);
  if (idx >= 0 && idx < PHASE_ORDER.length - 1) return PHASE_ORDER[idx + 1];
  return null;
}

export const PhaseSelector: React.FC = () => {
  const { currentPhase, effortLevel, voiceEnabled, setPhase, setEffortLevel } = usePhaseStore();

  const handlePhaseClick = (phase: AlgorithmPhase) => {
    setPhase(phase);
    if (voiceEnabled) {
      speak(`Entering the ${formatPhaseLabel(phase)} phase`);
    }
  };

  const handleEffortChange = (level: EffortLevel) => {
    setEffortLevel(level);
  };

  const nextPhase = getNextPhase(currentPhase);

  return (
    <div className="phase-selector">
      <div className="phase-buttons">
        {PHASE_ORDER.filter((p) => p !== 'complete').map((phase) => (
          <button
            key={phase}
            className={`phase-btn ${currentPhase === phase ? 'active' : ''}`}
            onClick={() => handlePhaseClick(phase)}
            title={formatPhaseLabel(phase)}
          >
            {formatPhaseLabel(phase).slice(0, 3)}
          </button>
        ))}
      </div>
      <div className="phase-controls">
        <select
          value={effortLevel}
          onChange={(e) => handleEffortChange(e.target.value as EffortLevel)}
          className="effort-select"
          title="Effort level"
        >
          {EFFORT_LEVELS.map((el) => (
            <option key={el.value} value={el.value}>{el.label}</option>
          ))}
        </select>
        {nextPhase && (
          <button
            className="phase-next-btn"
            onClick={() => handlePhaseClick(nextPhase)}
            title={`Next: ${formatPhaseLabel(nextPhase)}`}
          >
            Next: {formatPhaseLabel(nextPhase).slice(0, 3)}
          </button>
        )}
      </div>
    </div>
  );
};

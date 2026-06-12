import React, { useEffect, useState } from 'react';
import { useChatStore } from '../../store/chatStore';
import { useISOStore } from '../../store/isoStore';
import { usePhaseStore, formatPhaseLabel } from '../../store/phaseStore';

function formatUptime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export const StatusBar: React.FC = () => {
  const {
    isConnected, apiState, apiDetail,
    brainUptime, brainTokenCount, brainAuditCount, brainActiveISO,
    pollBrainStatus
  } = useChatStore();
  const { rules, vanEngineAvailable } = useISOStore();
  const { currentPhase, effortLevel, criteria } = usePhaseStore();
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const clock = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    const poll = setInterval(() => {
      useChatStore.getState().pollBrainStatus();
    }, 15000);
    useChatStore.getState().pollBrainStatus();
    return () => { clearInterval(clock); clearInterval(poll); };
  }, []);

  const violatedRules = rules.filter(r => r.status === 'violated').length;
  const activeRules = rules.filter(r => r.status === 'active' || r.status === 'enforced').length;
  const doneCount = criteria.filter((c) => c.done).length;
  const totalCount = criteria.length;

  return (
    <div className="status-bar">
      <div className="status-left">
        <span className={`status-item ${apiState === 'ready' ? 'active' : apiState === 'starting' ? 'warning' : ''}`}>
          Brain: {apiState === 'ready' ? 'Ready' : apiState === 'starting' ? 'Starting' : apiState === 'error' ? 'Offline' : 'Idle'}
        </span>
        <span className={`status-item ${vanEngineAvailable ? 'active' : 'warning'}`}>
          VAN: {vanEngineAvailable ? 'On' : 'Off'}
        </span>
        <span className={`status-item ${isConnected ? 'active' : ''}`}>
          Chat: {isConnected ? 'On' : 'Off'}
        </span>
        {apiState === 'ready' && (
          <>
            <span className="status-item">Uptime: {formatUptime(brainUptime)}</span>
            <span className="status-item">Tokens: {brainTokenCount}</span>
            <span className="status-item">Audits: {brainAuditCount}</span>
          </>
        )}
      </div>
      <div className="status-right">
        <span className="status-item">{formatPhaseLabel(currentPhase)}</span>
        <span className={`status-item effort-${effortLevel}`}>{effortLevel}</span>
        {totalCount > 0 && (
          <span className="status-item">{doneCount}/{totalCount} ISC</span>
        )}
        <span className="status-item" title={brainActiveISO.join(', ')}>
          ISO: {activeRules} a / {violatedRules} v
        </span>
        <span className="status-item">
          {apiDetail || 'Waiting for brain'}
        </span>
        <span className="status-item">
          {time}
        </span>
      </div>
    </div>
  );
};

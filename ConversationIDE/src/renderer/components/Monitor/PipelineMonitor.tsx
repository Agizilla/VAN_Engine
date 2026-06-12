import React, { useState } from 'react';
import { useWebSocketMonitor } from '../../hooks/useWebSocketMonitor';

export const PipelineMonitor: React.FC = () => {
  const { isConnected, executions, stats, startPipeline, refresh } = useWebSocketMonitor();
  const [pipelineName, setPipelineName] = useState('');
  const [agentName, setAgentName] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const handleStartPipeline = async () => {
    if (!pipelineName.trim()) return;
    setIsStarting(true);
    try {
      await startPipeline(pipelineName, agentName || 'cli', [
        { id: 'step-1', action: 'analyze' },
        { id: 'step-2', action: 'process' }
      ]);
      setPipelineName('');
      setTimeout(refresh, 500);
    } finally {
      setIsStarting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '\u25B6\uFE0F';
      case 'completed': return '\u2705';
      case 'failed': return '\u274C';
      default: return '\u23F8\uFE0F';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'var(--accent-cyan)';
      case 'completed': return 'var(--success)';
      case 'failed': return 'var(--error)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div className="pipeline-monitor">
      <div className="monitor-header">
        <h2>Pipeline Monitor</h2>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      <div className="stats-panel">
        <div className="stat-card"><div className="stat-value">{stats.total}</div><div className="stat-label">Total</div></div>
        <div className="stat-card"><div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>{stats.running}</div><div className="stat-label">Running</div></div>
        <div className="stat-card"><div className="stat-value" style={{ color: 'var(--success)' }}>{stats.completed}</div><div className="stat-label">Completed</div></div>
        <div className="stat-card"><div className="stat-value" style={{ color: 'var(--error)' }}>{stats.failed}</div><div className="stat-label">Failed</div></div>
      </div>

      <div className="control-panel">
        <h3>Start New Pipeline</h3>
        <div className="control-form">
          <input type="text" value={pipelineName} onChange={(e) => setPipelineName(e.target.value)} placeholder="Pipeline name" />
          <input type="text" value={agentName} onChange={(e) => setAgentName(e.target.value)} placeholder="Agent name (optional)" />
          <button onClick={handleStartPipeline} disabled={isStarting || !pipelineName.trim()}>
            {isStarting ? 'Starting...' : 'Start Pipeline'}
          </button>
        </div>
      </div>

      <div className="executions-list">
        <h3>Active Executions</h3>
        {executions.length === 0 ? (
          <div className="empty-state">No active executions</div>
        ) : (
          executions.map((exec) => (
            <div key={exec.id} className={`execution-card ${exec.status}`}>
              <div className="execution-header">
                <div className="execution-info">
                  <span className="execution-id">{exec.id.substring(0, 8)}</span>
                  <span className="execution-pipeline">{exec.pipeline}</span>
                </div>
                <div className="execution-status" style={{ color: getStatusColor(exec.status) }}>
                  {getStatusIcon(exec.status)} {exec.status}
                </div>
              </div>
              <div className="execution-details">
                <span>Agent: {exec.agent}</span>
                <span>Steps: {exec.steps.length}</span>
              </div>
              <div className="steps-progress">
                {exec.steps.map((step) => (
                  <div key={step.id} className={`step-dot ${step.status}`}
                    title={`${step.action}: ${step.status}`} />
                ))}
              </div>
              {exec.error && <div className="execution-error">{exec.error}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

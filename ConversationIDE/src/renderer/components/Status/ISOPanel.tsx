import React, { useEffect } from 'react';
import { useISOStore } from '../../store/isoStore';

export const ISOPanel: React.FC = () => {
  const { rules, auditEvents, checkRule } = useISOStore();

  useEffect(() => {
    const interval = setInterval(() => {
      rules.forEach(rule => checkRule(rule.id));
    }, 30000);
    return () => clearInterval(interval);
  }, [rules.length]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'ACTIVE';
      case 'violated': return 'VIOLATED';
      case 'enforced': return 'ENFORCED';
      case 'checking': return 'CHECKING';
      default: return 'UNKNOWN';
    }
  };

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'active': return '🟢';
      case 'violated': return '🔴';
      case 'enforced': return '🟡';
      case 'checking': return '🟠';
      default: return '⚪';
    }
  };

  return (
    <div className="iso-panel">
      <h3>ISO Rules</h3>
      <div className="iso-grid">
        {rules.map(rule => (
          <div key={rule.id} className={`iso-card ${rule.status}`}>
            <div className="iso-header">
              <span className="iso-id">{rule.id}</span>
              <span className="iso-status">{getStatusIndicator(rule.status)}</span>
            </div>
            <div className="iso-name">{rule.name}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {getStatusColor(rule.status)}
            </div>
          </div>
        ))}
      </div>

      <div className="audit-section">
        <h4>Recent Audit</h4>
        <div className="audit-list">
          {auditEvents.length === 0 ? (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>No audit events yet</div>
          ) : (
            auditEvents.slice(-10).reverse().map(event => (
              <div key={event.id} className="audit-item">
                <span className="audit-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
                <span className="audit-component">{event.component}</span>
                <span className="audit-action">{event.action}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

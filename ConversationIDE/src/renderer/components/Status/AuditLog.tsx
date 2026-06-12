import React, { useEffect, useState } from 'react';
import { useISOStore } from '../../store/isoStore';

export const AuditLog: React.FC = () => {
  const { auditEvents } = useISOStore();
  const [filter, setFilter] = useState<string>('all');

  const filteredEvents = filter === 'all'
    ? auditEvents
    : auditEvents.filter(e => e.component === filter);

  const uniqueComponents = [...new Set(auditEvents.map(e => e.component))];

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Audit Log</h3>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ width: 'auto', fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
        >
          <option value="all">All Components</option>
          {uniqueComponents.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="audit-list" style={{ maxHeight: '300px' }}>
        {filteredEvents.length === 0 ? (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '1rem', textAlign: 'center' }}>
            No audit events to display
          </div>
        ) : (
          filteredEvents.slice(-50).reverse().map(event => (
            <div key={event.id} className="audit-item">
              <span className="audit-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
              <span className="audit-component">{event.component}</span>
              <span className="audit-action">{event.action}</span>
              {event.magnitude_drift !== undefined && (
                <span className={`audit-drift ${event.magnitude_drift < 0.001 ? 'good' : 'bad'}`}>
                  {event.magnitude_drift.toExponential(2)}
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

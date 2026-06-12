import React, { useState } from 'react';

interface Bridge {
  id: string;
  name: string;
  enabled: boolean;
  type: string;
}

export const Bridges: React.FC = () => {
  const [bridges, setBridges] = useState<Bridge[]>([
    { id: 'gemini', name: 'Gemini Bridge', enabled: false, type: 'api' },
    { id: 'deepseek', name: 'DeepSeek Bridge', enabled: false, type: 'api' },
    { id: 'openai', name: 'OpenAI Bridge', enabled: false, type: 'api' }
  ]);

  const toggleBridge = (id: string) => {
    setBridges(prev => prev.map(b =>
      b.id === id ? { ...b, enabled: !b.enabled } : b
    ));
  };

  const enabledCount = bridges.filter(b => b.enabled).length;

  return (
    <div className="settings-panel">
      <div className="settings-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h4>External Bridges</h4>
          <span style={{ fontSize: '0.75rem', color: 'var(--warning)' }}>
            ISO_019: {enabledCount === 0 ? 'Compliant' : 'Violated'}
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          All bridges are disabled by default (ISO_019 - Privacy by Default).
          Enabling external bridges requires explicit user consent.
        </p>
        {bridges.map(bridge => (
          <div key={bridge.id} className="setting-row">
            <div>
              <span className="setting-label">{bridge.name}</span>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{bridge.type}</div>
            </div>
            <div
              className={`toggle-switch ${bridge.enabled ? 'active' : ''}`}
              onClick={() => toggleBridge(bridge.id)}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

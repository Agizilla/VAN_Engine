import React, { useState } from 'react';

interface AppSettings {
  theme: 'dark' | 'light';
  fontSize: number;
  voiceEnabled: boolean;
  autoSave: boolean;
  offlineOnly: boolean;
}

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>({
    theme: 'dark',
    fontSize: 14,
    voiceEnabled: true,
    autoSave: true,
    offlineOnly: true
  });

  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="settings-panel">
      <h3 style={{ color: 'var(--accent-cyan)', marginBottom: '1rem' }}>Settings</h3>

      <div className="settings-section">
        <h4>Appearance</h4>
        <div className="setting-row">
          <span className="setting-label">Theme</span>
          <select
            value={settings.theme}
            onChange={(e) => updateSetting('theme', e.target.value as 'dark' | 'light')}
            style={{ width: 'auto' }}
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
        <div className="setting-row">
          <span className="setting-label">Font Size</span>
          <input
            type="number"
            value={settings.fontSize}
            onChange={(e) => updateSetting('fontSize', Number(e.target.value))}
            min={10}
            max={24}
            style={{ width: '60px' }}
          />
        </div>
      </div>

      <div className="settings-section">
        <h4>Features</h4>
        <div className="setting-row">
          <span className="setting-label">Voice Commands</span>
          <div
            className={`toggle-switch ${settings.voiceEnabled ? 'active' : ''}`}
            onClick={() => updateSetting('voiceEnabled', !settings.voiceEnabled)}
          />
        </div>
        <div className="setting-row">
          <span className="setting-label">Auto Save</span>
          <div
            className={`toggle-switch ${settings.autoSave ? 'active' : ''}`}
            onClick={() => updateSetting('autoSave', !settings.autoSave)}
          />
        </div>
        <div className="setting-row">
          <span className="setting-label">Offline Only (ISO_019)</span>
          <div
            className={`toggle-switch ${settings.offlineOnly ? 'active' : ''}`}
            onClick={() => updateSetting('offlineOnly', !settings.offlineOnly)}
          />
        </div>
      </div>

      <div className="settings-section">
        <h4>About</h4>
        <div className="setting-row">
          <span className="setting-label">Version</span>
          <span className="setting-value">1.0.0</span>
        </div>
        <div className="setting-row">
          <span className="setting-label">Engine</span>
          <span className="setting-value">VAN_Engine Substrate</span>
        </div>
      </div>
    </div>
  );
};

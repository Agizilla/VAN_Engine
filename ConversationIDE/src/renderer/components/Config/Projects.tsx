import React from 'react';

interface Project {
  id: string;
  name: string;
  root: string;
  type: string;
  iso_004_compliant: boolean;
}

export const Projects: React.FC = () => {
  const [projects] = React.useState<Project[]>([
    { id: 'van_engine', name: 'VAN_Engine', root: '../..', type: 'substrate', iso_004_compliant: true },
    { id: 'conversation_ide', name: 'Conversation-IDE', root: '.', type: 'vessel', iso_004_compliant: true }
  ]);

  return (
    <div className="settings-panel">
      <div className="settings-section">
        <h4>Active Projects</h4>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          ISO_004: Project isolation prevents cross-project mutations.
        </p>
        {projects.map(project => (
          <div key={project.id} style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '0.75rem',
            marginBottom: '0.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{project.name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{project.root}</div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{project.type}</span>
                {project.iso_004_compliant && (
                  <span style={{ fontSize: '0.7rem', color: 'var(--success)' }}>ISO_004 OK</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

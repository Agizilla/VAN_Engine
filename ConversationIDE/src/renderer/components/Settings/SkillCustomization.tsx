import React, { useState, useEffect } from 'react';

interface SkillInfo {
  name: string;
  hasCustomizations: boolean;
  customizationPath?: string;
}

export const SkillCustomization: React.FC = () => {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [customConfig, setCustomConfig] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    setIsLoading(true);
    try {
      const response = await window.electronAPI.skillLoader?.list();
      if (response) {
        setSkills(response);
      }
    } catch (err) {
      console.error('Failed to load skills:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCustomization = async (skillName: string) => {
    try {
      const response = await window.electronAPI.skillLoader?.getCustomization(skillName);
      if (response) {
        setCustomConfig(response.content || '{}');
      }
    } catch (err) {
      console.error('Failed to load customization:', err);
    }
  };

  const saveCustomization = async () => {
    if (!selectedSkill) return;
    try {
      await window.electronAPI.skillLoader?.saveCustomization(selectedSkill, customConfig);
      alert('Customization saved');
      loadSkills();
    } catch (err) {
      console.error('Failed to save customization:', err);
      alert('Failed to save customization');
    }
  };

  const createCustomization = async (skillName: string) => {
    try {
      await window.electronAPI.skillLoader?.createCustomization(skillName);
      loadSkills();
      setSelectedSkill(skillName);
      loadCustomization(skillName);
    } catch (err) {
      console.error('Failed to create customization:', err);
    }
  };

  return (
    <div className="skill-customization">
      <h2>Skill Customization</h2>
      <p className="subtitle">Override skill configurations with user preferences</p>

      <div className="skills-list">
        <h3>Available Skills</h3>
        {isLoading ? (
          <div className="loading">Loading skills...</div>
        ) : (
          <div className="skill-items">
            {skills.map((skill) => (
              <div key={skill.name} className={`skill-item ${selectedSkill === skill.name ? 'selected' : ''}`}
                onClick={() => { setSelectedSkill(skill.name); loadCustomization(skill.name); }}>
                <span className="skill-name">{skill.name}</span>
                {skill.hasCustomizations ? (
                  <span className="custom-badge">Customized</span>
                ) : (
                  <button className="create-btn" onClick={(e) => { e.stopPropagation(); createCustomization(skill.name); }}>
                    Create
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedSkill && (
        <div className="customization-editor">
          <div className="editor-header">
            <h3>{selectedSkill} Configuration</h3>
            <button onClick={saveCustomization} className="save-btn">Save Customization</button>
          </div>
          <textarea value={customConfig} onChange={(e) => setCustomConfig(e.target.value)}
            placeholder='{\n  // Your custom configuration here\n}' rows={15} />
          <div className="editor-hint">
            <p>This configuration will override the base skill config when loaded.</p>
            <p>The base skill config is never modified. Customizations are stored separately.</p>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { useFileStore } from '../../store/fileStore';

export const Editor: React.FC = () => {
  const { activeFile, activeFileContent, setActiveFileContent, writeFile, loadTree } = useFileStore();
  const [editedContent, setEditedContent] = useState<string>('');
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (activeFileContent !== null) {
      setEditedContent(activeFileContent);
      setIsDirty(false);
    }
  }, [activeFileContent, activeFile?.path]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditedContent(e.target.value);
    setIsDirty(true);
  };

  const handleSave = async () => {
    if (activeFile && isDirty) {
      await writeFile(activeFile.path, editedContent);
      setActiveFileContent(editedContent);
      setIsDirty(false);
      if (activeFile.path) {
        const parentPath = activeFile.path.split('/').slice(0, -1).join('/');
        if (parentPath) loadTree(parentPath);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave();
    }
  };

  if (!activeFile) {
    return (
      <div className="editor-panel">
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <div className="empty-state-text">Select a file to edit</div>
        </div>
      </div>
    );
  }

  return (
    <div className="editor-panel">
      <div className="editor-tabs">
        <div className="editor-tab active">
          {activeFile.name} {isDirty && '*'}
        </div>
      </div>
      <div className="editor-content">
        <textarea
          value={editedContent}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          style={{
            width: '100%',
            height: '100%',
            background: 'var(--bg-primary)',
            color: 'var(--text-primary)',
            border: 'none',
            padding: '1rem',
            fontFamily: 'monospace',
            fontSize: '0.85rem',
            resize: 'none',
            outline: 'none'
          }}
          spellCheck={false}
        />
      </div>
      {isDirty && (
        <div style={{ padding: '0.3rem 1rem', background: 'var(--bg-card)', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--warning)' }}>Unsaved changes</span>
          <button onClick={handleSave} style={{ padding: '0.2rem 0.8rem', fontSize: '0.75rem' }}>Save (Ctrl+S)</button>
        </div>
      )}
    </div>
  );
};

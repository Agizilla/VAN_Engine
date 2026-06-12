import React, { useState, useEffect } from 'react';
import { useFileStore } from '../../store/fileStore';

interface FileTreeProps {
  rootPath: string;
  onFileSelect: (path: string) => void;
}

export const FileTree: React.FC<FileTreeProps> = ({ rootPath, onFileSelect }) => {
  const { tree, loadTree, createFile, deleteFile, isLoading } = useFileStore();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadTree(rootPath);
  }, [rootPath]);

  const toggleExpand = (path: string) => {
    const newExpanded = new Set(expanded);
    if (expanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpanded(newExpanded);
  };

  const renderNode = (node: any, depth: number = 0) => {
    if (!node) return null;
    const isExpanded = expanded.has(node.path);

    return (
      <div key={node.path}>
        <div
          className={`file-node ${node.type}`}
          onClick={() => node.type === 'file' ? onFileSelect(node.path) : toggleExpand(node.path)}
          style={{ paddingLeft: 8 + depth * 16 }}
        >
          <span className="expand-icon">
            {node.type === 'directory' ? (isExpanded ? '📂' : '📁') : '📄'}
          </span>
          <span className="file-name">{node.name}</span>
          {node.isWatched && <span className="watch-badge">W</span>}
        </div>
        {node.type === 'directory' && isExpanded && node.children?.map((child: any) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="file-tree">
      <div className="file-tree-header">
        <h3>Project Files</h3>
        <div style={{ display: 'flex', gap: '0.3rem' }}>
          <button onClick={() => createFile(rootPath, 'new_file.txt')} style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}>+</button>
        </div>
      </div>
      <div className="file-tree-content">
        {isLoading ? (
          <div className="loading">Loading...</div>
        ) : tree ? (
          renderNode(tree)
        ) : (
          <div className="empty-state">
            <div className="empty-state-text">No files loaded</div>
          </div>
        )}
      </div>
    </div>
  );
};

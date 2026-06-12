import React from 'react';

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged' | 'header';
  content: string;
}

interface DiffViewerProps {
  originalContent: string;
  modifiedContent: string;
  fileName?: string;
}

function computeDiff(original: string, modified: string): DiffLine[] {
  const origLines = original.split('\n');
  const modLines = modified.split('\n');
  const maxLen = Math.max(origLines.length, modLines.length);
  const lines: DiffLine[] = [];

  lines.push({ type: 'header', content: `--- Original${origLines.length} lines` });
  lines.push({ type: 'header', content: `+++ Modified${modLines.length} lines` });

  for (let i = 0; i < maxLen; i++) {
    if (i >= origLines.length) {
      lines.push({ type: 'added', content: `+ ${modLines[i]}` });
    } else if (i >= modLines.length) {
      lines.push({ type: 'removed', content: `- ${origLines[i]}` });
    } else if (origLines[i] !== modLines[i]) {
      lines.push({ type: 'removed', content: `- ${origLines[i]}` });
      lines.push({ type: 'added', content: `+ ${modLines[i]}` });
    } else {
      lines.push({ type: 'unchanged', content: `  ${origLines[i]}` });
    }
  }

  return lines;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ originalContent, modifiedContent, fileName }) => {
  const diffLines = computeDiff(originalContent, modifiedContent);

  return (
    <div className="diff-viewer">
      <div className="diff-pane">
        {diffLines.map((line, i) => (
          <div key={i} className={`diff-line ${line.type}`}>
            {line.content}
          </div>
        ))}
      </div>
    </div>
  );
};

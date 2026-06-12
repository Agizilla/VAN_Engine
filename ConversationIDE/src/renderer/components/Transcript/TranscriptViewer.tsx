import React, { useState } from 'react';

interface TranscriptMessage {
  role: string;
  content: string;
  timestamp?: string;
}

interface ParsedTranscript {
  last_message: string;
  voice_completion: string;
  plain_completion: string;
  response_state: string;
  message_count: number;
  messages: TranscriptMessage[];
}

export const TranscriptViewer: React.FC = () => {
  const [transcriptPath, setTranscriptPath] = useState<string>('');
  const [transcript, setTranscript] = useState<ParsedTranscript | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTranscript = async () => {
    if (!transcriptPath) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await window.electronAPI.transcript?.parse(transcriptPath);
      if (result) {
        setTranscript(result);
      } else {
        setError('Failed to parse transcript');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'awaiting_input': return '\u2753';
      case 'completed': return '\u2705';
      case 'error': return '\u274C';
      default: return '\u26AA';
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'awaiting_input': return '#fbbf24';
      case 'completed': return '#4ade80';
      case 'error': return '#f87171';
      default: return '#94a3b8';
    }
  };

  return (
    <div className="transcript-viewer">
      <h2>Transcript Viewer</h2>
      <p className="subtitle">Parse Claude Code session transcripts</p>

      <div className="input-section">
        <input type="text" value={transcriptPath}
          onChange={(e) => setTranscriptPath(e.target.value)}
          placeholder="Path to transcript JSONL file" className="path-input" />
        <button onClick={loadTranscript} disabled={isLoading || !transcriptPath}>
          {isLoading ? 'Loading...' : 'Parse Transcript'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {transcript && (
        <div className="transcript-content">
          <div className="summary-bar">
            <div className="summary-item">
              <span className="summary-label">Messages</span>
              <span className="summary-value">{transcript.message_count}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">State</span>
              <span className="summary-value" style={{ color: getStateColor(transcript.response_state) }}>
                {getStateIcon(transcript.response_state)} {transcript.response_state}
              </span>
            </div>
          </div>

          {transcript.voice_completion && (
            <div className="voice-section">
              <h3>Voice Completion</h3>
              <div className="voice-text">{transcript.voice_completion}</div>
            </div>
          )}

          {transcript.plain_completion && (
            <div className="plain-section">
              <h3>Plain Completion</h3>
              <div className="plain-text">{transcript.plain_completion}</div>
            </div>
          )}

          <div className="messages-section">
            <h3>Messages ({transcript.message_count})</h3>
            <div className="messages-list">
              {transcript.messages.map((msg, idx) => (
                <div key={idx} className={`message-bubble ${msg.role}`}>
                  <div className="message-header">
                    <span className="message-role">{msg.role === 'user' ? 'User' : 'Assistant'}</span>
                    {msg.timestamp && <span className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>}
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))}
            </div>
          </div>

          <details className="raw-section">
            <summary>Raw Last Message</summary>
            <pre>{transcript.last_message}</pre>
          </details>
        </div>
      )}
    </div>
  );
};

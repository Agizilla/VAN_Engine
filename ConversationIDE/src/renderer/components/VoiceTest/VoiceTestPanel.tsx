import React, { useState } from 'react';

const electronAPI = (window as any).electronAPI;

export const VoiceTestPanel: React.FC = () => {
  const [text, setText] = useState('Hello! This is a test of StyleTTS 2 voice synthesis.');
  const [voiceName, setVoiceName] = useState('male');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSynthesize = async () => {
    setLoading(true);
    setResult('');
    try {
      const res = await electronAPI.voice.synthesize(text, voiceName);
      if (res.ok) {
        setResult(`Audio generated: ${res.outputPath}`);
      } else {
        setResult(`Error: ${res.error}`);
      }
    } catch (err: any) {
      setResult(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 16 }}>
      <h3>StyleTTS 2 Voice</h3>
      <div style={{ marginBottom: 8 }}>
        <label>Text:</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          style={{ width: '100%', fontFamily: 'monospace' }}
        />
      </div>
      <div style={{ marginBottom: 8 }}>
        <label>Voice: </label>
        <input value={voiceName} onChange={(e) => setVoiceName(e.target.value)} style={{ fontFamily: 'monospace' }} />
      </div>
      <button onClick={handleSynthesize} disabled={loading}>
        {loading ? 'Synthesizing...' : 'Synthesize'}
      </button>
      {result && (
        <pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{result}</pre>
      )}
    </div>
  );
};

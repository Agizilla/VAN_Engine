import React from 'react';
import { useVoiceCommands, speak } from '../../hooks/useVoiceCommands';

interface VoiceInputProps {
  onSend: (message: string) => void;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onSend }) => {
  const { isListening, startListening, stopListening, transcript } = useVoiceCommands((command) => {
    onSend(command);
  });

  return (
    <div className="voice-input">
      <button
        onClick={isListening ? stopListening : startListening}
        style={{ background: isListening ? 'var(--error)' : undefined }}
      >
        {isListening ? 'Stop' : 'Record'}
      </button>
      {isListening && <span className="voice-indicator">Listening...</span>}
      {transcript && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{transcript}</span>}
      <button onClick={() => speak('Ready for your command')}>
        Test Voice
      </button>
    </div>
  );
};

export default VoiceInput;

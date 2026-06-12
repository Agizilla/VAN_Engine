import React, { useState } from 'react';
import { useChatStore, MessageIntent } from '../../store/chatStore';
import { usePhaseStore } from '../../store/phaseStore';
import MessageList from './MessageList';
import InputArea from './InputArea';
import VoiceInput from './VoiceInput';
import { PhaseSelector } from './PhaseSelector';

export const ChatPanel: React.FC = () => {
  const { currentConversation, sendMessage, isConnected, apiState, apiDetail } = useChatStore();
  const { addCriterion, currentPhase } = usePhaseStore();
  const messages = currentConversation?.messages || [];
  const [isVoiceMode, setIsVoiceMode] = useState(false);

  const handleSend = (content: string) => {
    if (!content.trim()) return;
    sendMessage(content);

    const intent = classifySimple(content);
    if (intent === 'task' && currentPhase !== 'observe' && currentPhase !== 'think') {
      addCriterion(content.slice(0, 80));
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h3>Conversation</h3>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button onClick={() => setIsVoiceMode(!isVoiceMode)}>
            {isVoiceMode ? 'Keyboard' : 'Voice'}
          </button>
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {apiState === 'starting' ? 'Brain starting' : isConnected ? 'Brain ready' : 'Brain offline'}
          </span>
        </div>
      </div>

      <PhaseSelector />

      <div style={{ padding: '0 1rem 0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        {apiDetail || 'Local brain will auto-start when you send the first message.'}
      </div>

      <MessageList messages={messages} />

      {isVoiceMode ? (
        <VoiceInput onSend={handleSend} />
      ) : (
        <InputArea onSend={handleSend} />
      )}
    </div>
  );
};

function classifySimple(content: string): MessageIntent {
  const lower = content.toLowerCase();
  if (/build|implement|create|add|fix|refactor|update|write|make/.test(lower)) return 'task';
  if (lower.includes('?') && lower.length < 200) return 'question';
  if (/run |execute |start |stop |deploy /.test(lower)) return 'command';
  return 'conversation';
}

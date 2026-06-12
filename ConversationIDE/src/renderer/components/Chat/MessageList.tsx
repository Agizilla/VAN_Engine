import React, { useRef, useEffect } from 'react';
import type { ChatMessage } from '../../store/chatStore';

interface MessageListProps {
  messages: ChatMessage[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className="message-list">
        <div className="empty-state">
          <div className="empty-state-icon">💬</div>
          <div className="empty-state-text">Start a conversation to begin</div>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.role}`}>
          <div className="message-bubble">{msg.content}</div>
          <div className="message-meta">
            {new Date(msg.timestamp).toLocaleTimeString()}
            {msg.metadata?.intent && ` · ${msg.metadata.intent}`}
            {msg.metadata?.confidence && ` · ${(msg.metadata.confidence * 100).toFixed(0)}%`}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;

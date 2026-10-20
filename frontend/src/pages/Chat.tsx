import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from 'react-query';
import axios from 'axios';
import { Send, Trash2 } from 'lucide-react';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Chat() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const chatMutation = useMutation(
    (msg: string) => axios.post(`${API_URL}/chat`, { message: msg }),
    {
      onSuccess: (data) => {
        setMessages([...messages, {
          user: data.data.user_message,
          assistant: data.data.assistant_response,
          timestamp: new Date().toLocaleTimeString()
        }]);
      },
      onError: (error: any) => {
        alert('Error: ' + (error.response?.data?.detail || 'Chat failed'));
      }
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !chatMutation.isPending) {
      chatMutation.mutate(message);
      setMessage('');
    }
  };

  return (
    <div className="page">
      <h1>Chat with Qwen AI</h1>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        💡 Tip: Make sure LM Studio is running with Qwen model for AI responses
      </p>

      <div style={{
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '12px',
        height: '500px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          {messages.length === 0 ? (
            <div style={{
              textAlign: 'center',
              color: '#999',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%'
            }}>
              <p>Start a conversation with Qwen AI</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx}>
                <div style={{
                  background: '#667eea',
                  color: 'white',
                  padding: '0.75rem 1rem',
                  borderRadius: '12px',
                  maxWidth: '70%',
                  marginLeft: 'auto',
                  wordWrap: 'break-word'
                }}>
                  <p style={{ margin: 0 }}>{msg.user}</p>
                  <small style={{ opacity: 0.7 }}>{msg.timestamp}</small>
                </div>
                <div style={{
                  background: '#f0f0f0',
                  color: '#333',
                  padding: '0.75rem 1rem',
                  borderRadius: '12px',
                  maxWidth: '70%',
                  wordWrap: 'break-word',
                  marginTop: '0.5rem'
                }}>
                  <p style={{ margin: 0 }}>{msg.assistant}</p>
                </div>
              </div>
            ))
          )}
          {chatMutation.isPending && (
            <div style={{ color: '#667eea', fontStyle: 'italic' }}>
              Qwen is thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} style={{
          borderTop: '1px solid #eee',
          padding: '1rem',
          display: 'flex',
          gap: '0.75rem'
        }}>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask Qwen something..."
            disabled={chatMutation.isPending}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '1rem'
            }}
          />
          <button
            type="submit"
            disabled={chatMutation.isPending}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: chatMutation.isPending ? 'not-allowed' : 'pointer',
              opacity: chatMutation.isPending ? 0.5 : 1
            }}
          >
            <Send size={20} />
          </button>
        </form>
      </div>

      {messages.length > 0 && (
        <button
          onClick={() => setMessages([])}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            background: '#ff4757',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Trash2 size={16} /> Clear Chat
        </button>
      )}
    </div>
  );
}

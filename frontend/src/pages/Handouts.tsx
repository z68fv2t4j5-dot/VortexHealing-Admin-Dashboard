import React, { useState } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { Search, MessageCircle, BookOpen } from 'lucide-react';
import '../styles/Pages.css';

export default function Handouts() {
  const [mode, setMode] = useState<'search' | 'ask'>('ask');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const { data: handoutsList } = useQuery('handouts-list', () =>
    axios.get(`/api/handouts/list`).then(r => r.data).catch(() => ({ count: 0, documents: [] }))
  );

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    try {
      const response = await axios.get(`/api/handouts/search`, {
        params: { q: searchTerm }
      });
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    }
    setLoading(false);
  };

  const handleAsk = async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(`/api/handouts/ask`, {
        question: searchTerm
      });
      setAnswer(response.data.answer);
      setSources(response.data.sources);
    } catch (error) {
      console.error('Ask error:', error);
      setAnswer('Error getting answer. Make sure Qwen is running.');
    }
    setLoading(false);
  };

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={28} /> Handouts Knowledge Base
        </h1>
        <p style={{ color: '#666', marginTop: '0.5rem' }}>
          {handoutsList?.count || 0} documents indexed • Search or ask questions
        </p>
      </div>

      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        <button
          onClick={() => { setMode('ask'); setAnswer(''); setSources([]); }}
          style={{
            padding: '0.75rem 1.5rem',
            background: mode === 'ask' ? '#667eea' : '#f0f0f0',
            color: mode === 'ask' ? 'white' : '#333',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <MessageCircle size={18} /> Ask (AI)
        </button>
        <button
          onClick={() => { setMode('search'); setSearchResults([]); }}
          style={{
            padding: '0.75rem 1.5rem',
            background: mode === 'search' ? '#667eea' : '#f0f0f0',
            color: mode === 'search' ? 'white' : '#333',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Search size={18} /> Search
        </button>
      </div>

      {/* Input Section */}
      <div style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (mode === 'search' ? handleSearch() : handleAsk())}
            placeholder={mode === 'ask' ? 'Ask a question about the handouts...' : 'Search handouts...'}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '1rem'
            }}
            disabled={loading}
          />
          <button
            onClick={mode === 'search' ? handleSearch : handleAsk}
            disabled={!searchTerm.trim() || loading}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '500',
              opacity: (!searchTerm.trim() || loading) ? 0.6 : 1
            }}
          >
            {loading ? '⏳' : mode === 'search' ? '🔍 Search' : '💭 Ask'}
          </button>
        </div>
      </div>

      {/* Ask Mode Results */}
      {mode === 'ask' && answer && (
        <div style={{
          background: 'white',
          padding: '1.5rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ marginTop: 0, color: '#667eea' }}>Answer</h3>
          <p style={{ color: '#333', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
            {answer}
          </p>

          {sources.length > 0 && (
            <>
              <h4 style={{ marginTop: '1.5rem', color: '#666' }}>Sources</h4>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {sources.map((source, idx) => (
                  <div key={idx} style={{
                    padding: '0.75rem',
                    background: '#f9f9f9',
                    borderLeft: '4px solid #667eea',
                    borderRadius: '4px'
                  }}>
                    <p style={{ margin: 0, fontWeight: '500', color: '#333' }}>
                      📄 {source.filename}
                    </p>
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#666' }}>
                      Relevance: {source.relevance}/10
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Search Mode Results */}
      {mode === 'search' && searchResults.length > 0 && (
        <div style={{
          display: 'grid',
          gap: '1rem'
        }}>
          {searchResults.map((result, idx) => (
            <div key={idx} style={{
              background: 'white',
              padding: '1.5rem',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              borderLeft: '4px solid #667eea'
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>
                📄 {result.filename}
              </h3>
              <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: '#666' }}>
                📍 {result.relative_path} • Relevance: {result.score}/10
              </p>
              <p style={{ margin: 0, color: '#555', lineHeight: '1.5' }}>
                {result.preview}...
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!answer && searchResults.length === 0 && !loading && (
        <div style={{
          background: 'white',
          padding: '2rem',
          textAlign: 'center',
          borderRadius: '8px',
          color: '#999'
        }}>
          <BookOpen size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
          <p>{mode === 'ask' ? 'Ask a question about the handouts' : 'Search the handouts'}</p>
          <p style={{ fontSize: '0.9rem' }}>
            Type your {mode === 'ask' ? 'question' : 'search term'} and press Enter or click the button
          </p>
        </div>
      )}
    </div>
  );
}

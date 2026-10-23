import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { Search, MessageCircle, BookOpen, RefreshCw, Sparkles, ExternalLink } from 'lucide-react';
import '../styles/Pages.css';

type Mode = 'auto' | 'search' | 'ask';

interface Passage {
  chunk_id: number;
  text: string;
  heading_path: string;
  document_id: number;
  title: string;
  version: string;
  path: string;
  doc_date: string | null;
}

interface QueryResult {
  query: string;
  mode: 'search' | 'ask';
  passages: Passage[];
  answer: string | null;
  answer_error: string | null;
}

const card = { background: 'white', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' };

const MODES: { id: Mode; label: string; icon: React.ReactNode }[] = [
  { id: 'auto', label: 'Auto', icon: <Sparkles size={18} /> },
  { id: 'search', label: 'Search', icon: <Search size={18} /> },
  { id: 'ask', label: 'Ask (AI)', icon: <MessageCircle size={18} /> },
];

// Bold the query words inside a passage, ignoring short and common words.
function highlight(text: string, query: string) {
  const words = query.toLowerCase().match(/[a-z0-9’']{3,}/g) || [];
  if (!words.length) return text;
  const pattern = new RegExp(`(${words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  return text.split(pattern).map((part, i) =>
    words.includes(part.toLowerCase()) ? <mark key={i} style={{ background: '#e8eaff' }}>{part}</mark> : part
  );
}

// Turn [3] in an answer into a link that scrolls to passage 3.
function withCitations(answer: string) {
  return answer.split(/(\[\d+\])/g).map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    return m
      ? <a key={i} href={`#passage-${m[1]}`} style={{ color: '#667eea', fontWeight: 600, textDecoration: 'none' }}>{part}</a>
      : part;
  });
}

export default function Handouts() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>('auto');
  const [text, setText] = useState('');
  const [result, setResult] = useState<QueryResult | null>(null);
  const [history, setHistory] = useState<{ q: string; answer: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { data: status } = useQuery(
    'handouts-status',
    () => axios.get('/api/handouts/status').then(r => r.data).catch(() => null),
    { refetchInterval: (data: any) => (data?.scanning ? 3000 : false) }
  );

  const run = async () => {
    const q = text.trim();
    if (!q) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post<QueryResult>('/api/handouts/query', { q, mode, history: history.slice(-3) });
      setResult(data);
      if (data.answer) setHistory(h => [...h, { q, answer: data.answer as string }].slice(-3));
    } catch {
      setError('The handouts service did not respond. Is the backend running?');
    }
    setLoading(false);
  };

  const rescan = async () => {
    await axios.post('/api/handouts/rescan').catch(() => null);
    setTimeout(() => queryClient.invalidateQueries('handouts-status'), 500);
  };

  return (
    <div className="page">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={28} /> Handouts Knowledge Base
        </h1>
        <p style={{ color: '#666', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {status?.configured === false
            ? 'HANDOUTS_DIR is not set in backend/.env'
            : status
              ? `${status.documents} handouts • ${status.chunks} passages • ${status.retired} older versions retired`
              : 'Index status unavailable'}
          {status?.scanning && <span style={{ color: '#667eea' }}>Scanning…</span>}
          {status?.last_scan && !status.scanning && (
            <span style={{ fontSize: '0.85rem', color: '#999' }}>last scan {status.last_scan.replace('T', ' ')}</span>
          )}
          <button
            onClick={rescan}
            disabled={status?.scanning}
            title="Look for new or changed handouts"
            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.35rem 0.75rem', background: '#f0f0f0',
              border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            <RefreshCw size={14} /> Rescan
          </button>
        </p>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        {MODES.map(m => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            style={{ padding: '0.6rem 1.25rem', background: mode === m.id ? '#667eea' : '#f0f0f0',
              color: mode === m.id ? 'white' : '#333', border: 'none', borderRadius: '6px', cursor: 'pointer',
              fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {m.icon} {m.label}
          </button>
        ))}
      </div>

      <div style={{ ...card, marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()}
            placeholder="Search a term, or ask a question about the handouts…"
            style={{ flex: 1, padding: '0.75rem 1rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem' }}
            disabled={loading}
          />
          <button
            onClick={run}
            disabled={!text.trim() || loading}
            style={{ padding: '0.75rem 1.5rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px',
              cursor: 'pointer', fontWeight: 500, opacity: !text.trim() || loading ? 0.6 : 1 }}
          >
            {loading ? (mode === 'search' ? 'Searching…' : 'Thinking…') : 'Go'}
          </button>
        </div>
        {mode !== 'search' && (
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#999' }}>
            Answers come only from the handouts, with numbered citations. They can take about a minute.
            {history.length > 0 && ' Follow-up questions use your previous question as context.'}
          </p>
        )}
      </div>

      {error && <div style={{ ...card, color: '#c0392b', marginBottom: '1.5rem' }}>{error}</div>}

      {result && (result.answer || result.answer_error) && (
        <div style={{ ...card, marginBottom: '1.5rem' }}>
          <h3 style={{ marginTop: 0, color: '#667eea' }}>Answer</h3>
          {result.answer_error
            ? <p style={{ color: '#c0392b' }}>{result.answer_error} The matching passages are below.</p>
            : <div style={{ color: '#333', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{withCitations(result.answer as string)}</div>}
        </div>
      )}

      {result && result.passages.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {result.passages.map((p, i) => (
            <div id={`passage-${i + 1}`} key={p.chunk_id} style={{ ...card, borderLeft: '4px solid #667eea' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'baseline' }}>
                <h3 style={{ margin: '0 0 0.35rem 0', color: '#333', fontSize: '1.05rem' }}>
                  <span style={{ color: '#667eea' }}>[{i + 1}]</span> {p.title}
                </h3>
                <a href={`/api/handouts/file/${p.document_id}`} target="_blank" rel="noreferrer"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem', color: '#667eea', whiteSpace: 'nowrap' }}>
                  Open handout <ExternalLink size={14} />
                </a>
              </div>
              <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.85rem', color: '#666' }}>
                {p.heading_path || 'Opening section'}
                {p.version && ` • version ${p.version}`}
                {p.doc_date && ` • ${p.doc_date}`}
              </p>
              <p style={{ margin: 0, color: '#555', lineHeight: 1.55 }}>{highlight(p.text, result.query)}</p>
            </div>
          ))}
        </div>
      )}

      {result && result.passages.length === 0 && (
        <div style={{ ...card, textAlign: 'center', color: '#999' }}>Nothing in the handouts matched “{result.query}”.</div>
      )}

      {!result && !loading && !error && (
        <div style={{ ...card, padding: '2rem', textAlign: 'center', color: '#999' }}>
          <BookOpen size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
          <p>Search for a tool or term, or ask a question such as “What is a karma knot?”</p>
          <p style={{ fontSize: '0.9rem' }}>Auto answers questions and searches everything else.</p>
        </div>
      )}
    </div>
  );
}

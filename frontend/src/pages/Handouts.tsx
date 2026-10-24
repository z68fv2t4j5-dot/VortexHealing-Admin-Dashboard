import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { Search, MessageCircle, BookOpen, RefreshCw, Sparkles, ExternalLink, Layers } from 'lucide-react';
import { EntityCard, EntityCardById, EntityCardData, KnowledgeBrowse } from '../components/HandoutsKnowledge';
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
  searchedAs: string;
  rewritten: boolean;
  searches: string[];
  passages: Passage[];
  answer: string;
  answerError: string;
  fallback: boolean;
  asked: boolean;
  cards: EntityCardData[];
}

type Phase = 'searching' | 'thinking' | 'writing' | null;

const card = { background: 'white', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' };

const MODES: { id: Mode; label: string; icon: React.ReactNode }[] = [
  { id: 'auto', label: 'Auto', icon: <Sparkles size={18} /> },
  { id: 'search', label: 'Search', icon: <Search size={18} /> },
  { id: 'ask', label: 'Ask (AI)', icon: <MessageCircle size={18} /> },
];

const COMMON = new Set(['and', 'the', 'what', 'which', 'does', 'how', 'why', 'who', 'when', 'where', 'class', 'with',
  'for', 'from', 'that', 'this', 'are', 'can', 'you', 'our', 'into', 'its', 'whats', 'should', 'used', 'get']);

// Mark the query words inside a passage, as whole words, ignoring short and common ones.
function highlight(text: string, query: string) {
  const words: string[] = (query.toLowerCase().match(/[a-z0-9’']{3,}/g) || []).filter(w => !COMMON.has(w));
  if (!words.length) return text;
  const pattern = new RegExp(`\\b(${words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  return text.split(pattern).map((part, i) =>
    words.includes(part.toLowerCase()) ? <mark key={i} style={{ background: '#e8eaff' }}>{part}</mark> : part
  );
}

// Inline answer text: **bold**, and [3] as a link that scrolls to passage 3.
function inline(text: string, key: string) {
  return text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, i) => {
    const cite = part.match(/^\[(\d+)\]$/);
    if (cite) {
      return <a key={`${key}-${i}`} href={`#passage-${cite[1]}`} style={{ color: '#667eea', fontWeight: 600, textDecoration: 'none' }}>{part}</a>;
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={`${key}-${i}`}>{part.slice(2, -2)}</strong>;
    return part;
  });
}

// The small amount of Markdown Qwen writes: headings, bullet and numbered lines, paragraphs.
function renderAnswer(answer: string) {
  return answer.split('\n').map((line, i) => {
    const key = String(i);
    const heading = line.match(/^#{1,6}\s+(.*)/);
    if (heading) return <h4 key={key} style={{ margin: '1rem 0 0.25rem', color: '#333' }}>{inline(heading[1], key)}</h4>;
    const bullet = line.match(/^\s*([-*•]|\d+[.)])\s+(.*)/);
    if (bullet) {
      return (
        <div key={key} style={{ display: 'flex', gap: '0.5rem', margin: '0.2rem 0 0.2rem 0.5rem' }}>
          <span style={{ color: '#667eea' }}>{/\d/.test(bullet[1]) ? bullet[1] : '•'}</span>
          <span>{inline(bullet[2], key)}</span>
        </div>
      );
    }
    if (!line.trim()) return <div key={key} style={{ height: '0.5rem' }} />;
    return <p key={key} style={{ margin: '0.25rem 0' }}>{inline(line, key)}</p>;
  });
}

export default function Handouts() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<Mode>('auto');
  const [text, setText] = useState('');
  const [result, setResult] = useState<QueryResult | null>(null);
  const [history, setHistory] = useState<{ q: string; answer: string }[]>([]);
  const [phase, setPhase] = useState<Phase>(null);
  const loading = phase !== null;
  const [error, setError] = useState('');
  const [view, setView] = useState<'ask' | 'browse'>('ask');
  const [openCard, setOpenCard] = useState<number | null>(null);

  const { data: status } = useQuery(
    'handouts-status',
    () => axios.get('/api/handouts/status').then(r => r.data).catch(() => null),
    { refetchInterval: (data: any) => (data?.scanning ? 3000 : data?.knowledge?.running ? 30000 : false) }
  );

  // Reads newline-delimited JSON events: passages first, then the answer as Qwen writes it.
  const run = async () => {
    const q = text.trim();
    if (!q) return;
    setPhase('searching');
    setError('');
    setOpenCard(null);
    let current: QueryResult = { query: q, searchedAs: q, rewritten: false, searches: [], passages: [],
      answer: '', answerError: '', fallback: false, asked: false, cards: [] };
    setResult(current);
    const update = (patch: Partial<QueryResult>) => { current = { ...current, ...patch }; setResult(current); };
    try {
      const response = await fetch('/api/handouts/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ q, mode, history: history.slice(-3) }),
      });
      if (!response.ok || !response.body) throw new Error(String(response.status));
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines.filter(Boolean)) {
          const event = JSON.parse(line);
          if (event.type === 'sources') {
            update({ searchedAs: event.question, rewritten: event.rewritten, searches: event.searches, passages: event.passages,
              cards: event.cards || [] });
          } else if (event.type === 'thinking') {
            update({ asked: true });
            setPhase('thinking');
          } else if (event.type === 'text') {
            update({ asked: true, answer: current.answer + event.text });
            setPhase('writing');
          } else if (event.type === 'error') {
            update({ asked: true, answerError: event.text });
          } else if (event.type === 'done' && event.answer) {
            update({ asked: true, answer: event.answer, fallback: event.fallback });
            if (!event.fallback) setHistory(h => [...h, { q: current.searchedAs, answer: event.answer }].slice(-3));
          }
        }
      }
    } catch {
      setError('The handouts service did not respond. Is the backend running?');
    }
    setPhase(null);
  };

  const buildMap = async () => {
    await axios.post('/api/handouts/knowledge/run').catch(() => null);
    setTimeout(() => queryClient.invalidateQueries('handouts-status'), 1000);
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
        {status?.knowledge && (
          <p style={{ color: '#999', margin: '0.25rem 0 0', fontSize: '0.85rem', display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            Knowledge map: {status.knowledge.entities} entries • {status.knowledge.facts} facts
            {status.knowledge.running
              ? <span style={{ color: '#667eea' }}>• being built ({status.knowledge.sections_unread} sections still to read)</span>
              : status.knowledge.sections_unread > 0 && (
                <>
                  <span>• {status.knowledge.sections_unread} sections not read yet</span>
                  <button onClick={buildMap} title="Qwen reads the new sections; this can take hours for many"
                    style={{ padding: '0.2rem 0.6rem', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}>
                    Build
                  </button>
                </>
              )}
          </p>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        {MODES.map(m => (
          <button
            key={m.id}
            onClick={() => { setMode(m.id); setView('ask'); }}
            style={{ padding: '0.6rem 1.25rem', background: view === 'ask' && mode === m.id ? '#667eea' : '#f0f0f0',
              color: view === 'ask' && mode === m.id ? 'white' : '#333', border: 'none', borderRadius: '6px', cursor: 'pointer',
              fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {m.icon} {m.label}
          </button>
        ))}
        <button
          onClick={() => setView('browse')}
          title="Every tool, class and kind of conditioning in the knowledge map"
          style={{ padding: '0.6rem 1.25rem', background: view === 'browse' ? '#667eea' : '#f0f0f0',
            color: view === 'browse' ? 'white' : '#333', border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: 'auto' }}
        >
          <Layers size={18} /> Browse
        </button>
      </div>

      {view === 'browse' ? <KnowledgeBrowse /> : (<>

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
            {phase === 'searching' ? 'Searching…' : phase === 'thinking' ? 'Thinking…' : phase === 'writing' ? 'Writing…' : 'Go'}
          </button>
        </div>
        {mode !== 'search' && (
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#999', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span>
              Answers come only from the handouts, with numbered citations; the passages appear first.
              {history.length > 0 && ' Follow-up questions understand the previous ones.'}
            </span>
            {history.length > 0 && !loading && (
              <button onClick={() => { setHistory([]); setResult(null); }}
                style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', fontSize: '0.8rem', padding: 0 }}>
                New topic
              </button>
            )}
          </p>
        )}
      </div>

      {error && <div style={{ ...card, color: '#c0392b', marginBottom: '1.5rem' }}>{error}</div>}

      {result && (result.rewritten || result.searches.length > 0) && (
        <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: '#666' }}>
          {result.rewritten && <>Understood as: <em>{result.searchedAs}</em></>}
          {result.searches.length > 0 && <>{result.rewritten && ' • '}Searched for: {result.searches.join(' · ')}</>}
        </p>
      )}

      {openCard !== null && (
        <div style={{ marginBottom: '1.5rem' }}><EntityCardById id={openCard} onOpen={setOpenCard} /></div>
      )}
      {openCard === null && result && result.cards.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
          {result.cards.map(c => <EntityCard key={c.id} data={c} onOpen={setOpenCard} />)}
        </div>
      )}

      {result && result.asked && (
        <div style={{ ...card, marginBottom: '1.5rem' }}>
          <h3 style={{ marginTop: 0, color: '#667eea' }}>Answer</h3>
          {result.answerError
            ? <p style={{ color: '#c0392b' }}>{result.answerError} The matching passages are below.</p>
            : result.fallback
              ? <p style={{ color: '#a0522d' }}>The answer did not cite its sources well enough to be trusted, so it is not shown. Read the passages below.</p>
              : result.answer
                ? <div style={{ color: '#333', lineHeight: 1.6 }}>{renderAnswer(result.answer)}</div>
                : <p style={{ color: '#999', margin: 0 }}>Reading the passages below…</p>}
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

      {result && !loading && result.passages.length === 0 && (
        <div style={{ ...card, textAlign: 'center', color: '#999' }}>Nothing in the handouts matched “{result.query}”.</div>
      )}

      {!result && !loading && !error && (
        <div style={{ ...card, padding: '2rem', textAlign: 'center', color: '#999' }}>
          <BookOpen size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
          <p>Search for a tool or term, or ask a question such as “What is a karma knot?”</p>
          <p style={{ fontSize: '0.9rem' }}>Auto answers questions and searches everything else.</p>
        </div>
      )}
      </>)}
    </div>
  );
}

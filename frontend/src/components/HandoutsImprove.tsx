import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { Play, Plus, CheckCircle2 } from 'lucide-react';
import { renderAnswer } from './AnswerText';
import { NoteDraft, NoteEditor } from './HandoutsNotes';

interface Question { q: string; expect?: string[]; history?: string[]; answer_should_say?: string; note?: string }
interface RunSummary {
  id: string; started: string; status: string; total: number; answered: number;
  Right: number; Partly: number; Wrong: number; unmarked: number; average_seconds: number | null;
}
interface RunItem {
  n: number; q: string; history: string[]; should_say: string | null; seconds: number | null;
  standalone?: string; answer?: string | null; answer_error?: string | null; fallback?: boolean;
  sources?: string[]; cards?: string[]; mark?: string | null; note?: string; note_file?: string;
}

const box = { background: 'white', padding: '1.25rem 1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' } as const;
const input = { width: '100%', padding: '0.5rem 0.7rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.95rem', fontFamily: 'inherit', boxSizing: 'border-box' } as const;
const MARK_COLOUR: Record<string, string> = { Right: '#2e8b57', Partly: '#c98a00', Wrong: '#c0392b' };
const when = (stamp: string) => stamp.replace('T', ' ').slice(0, 16);

function QuestionEditor({ initial, onSave, onCancel }: { initial: Question; onSave: (q: Question) => void; onCancel: () => void }) {
  const [q, setQ] = useState(initial.q);
  const [should, setShould] = useState(initial.answer_should_say || '');
  const [after, setAfter] = useState((initial.history || []).join(' | '));
  return (
    <div style={{ display: 'grid', gap: '0.5rem', padding: '0.75rem', background: '#f7f8fc', borderRadius: '6px' }}>
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="The question, as a student would ask it" style={input} autoFocus />
      <input value={should} onChange={e => setShould(e.target.value)} placeholder="What a right answer should say (optional)" style={input} />
      <input value={after} onChange={e => setAfter(e.target.value)} placeholder="Follow-up to which question? (optional; that question's exact words)" style={input} />
      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
        <button onClick={onCancel} style={{ padding: '0.4rem 0.9rem', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
        <button disabled={!q.trim()}
          onClick={() => onSave({ ...initial, q, answer_should_say: should, history: after.split('|').map(h => h.trim()).filter(Boolean) })}
          style={{ padding: '0.4rem 0.9rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          Save
        </button>
      </div>
    </div>
  );
}

function TestQuestions() {
  const queryClient = useQueryClient();
  const { data } = useQuery('improve-questions', () => axios.get('/api/handouts/eval/questions').then(r => r.data.questions as Question[]));
  const [editing, setEditing] = useState<number | 'new' | null>(null);
  const [open, setOpen] = useState(false);
  const refresh = () => { setEditing(null); queryClient.invalidateQueries('improve-questions'); };

  const save = async (index: number | 'new', q: Question) => {
    if (index === 'new') await axios.post('/api/handouts/eval/questions', q);
    else await axios.put(`/api/handouts/eval/questions/${index}`, q);
    refresh();
  };
  const remove = async (index: number, q: Question) => {
    if (!window.confirm(`Remove the test question "${q.q}"?`)) return;
    await axios.delete(`/api/handouts/eval/questions/${index}`);
    refresh();
  };

  return (
    <div style={box}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button onClick={() => setOpen(!open)} style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: '1.05rem', fontWeight: 600 }}>
          {open ? '▾' : '▸'} Test questions ({data?.length ?? '…'})
        </button>
        <button onClick={() => { setOpen(true); setEditing('new'); }}
          style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.4rem 0.9rem', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          <Plus size={15} /> Add a question
        </button>
      </div>
      {open && (
        <div style={{ display: 'grid', gap: '0.5rem', marginTop: '0.75rem' }}>
          {editing === 'new' && <QuestionEditor initial={{ q: '' }} onSave={q => save('new', q)} onCancel={() => setEditing(null)} />}
          {(data || []).map((q, i) => editing === i
            ? <QuestionEditor key={i} initial={q} onSave={nq => save(i, nq)} onCancel={() => setEditing(null)} />
            : (
              <div key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'baseline', borderBottom: '1px solid #f0f0f0', paddingBottom: '0.4rem' }}>
                <span style={{ color: '#999', minWidth: '1.5rem' }}>{i + 1}.</span>
                <span style={{ flex: 1 }}>
                  {q.q}
                  {q.history && q.history.length > 0 && <span style={{ color: '#999', fontSize: '0.85rem' }}> (follow-up to "{q.history.join('", "')}")</span>}
                  {q.answer_should_say && <div style={{ color: '#888', fontSize: '0.85rem' }}>Should say: {q.answer_should_say}</div>}
                </span>
                <button onClick={() => setEditing(i)} style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer' }}>Edit</button>
                <button onClick={() => remove(i, q)} style={{ background: 'none', border: 'none', color: '#c0392b', cursor: 'pointer' }}>Remove</button>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

function RunItemCard({ runId, item, onDraft }: { runId: string; item: RunItem; onDraft: (item: RunItem) => void }) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState(item.note || '');
  const [drafting, setDrafting] = useState(false);
  useEffect(() => setNote(item.note || ''), [item.note]);

  const save = async (mark: string | null | undefined, text?: string) => {
    await axios.put(`/api/handouts/eval/runs/${runId}/items/${item.n}`, { mark, note: text });
    queryClient.invalidateQueries(['improve-run', runId]);
    queryClient.invalidateQueries('improve-runs');
  };
  const draft = async () => {
    setDrafting(true);
    await save(item.mark, note);
    onDraft({ ...item, note });
    setDrafting(false);
  };

  if (item.seconds === null) {
    return <div style={{ ...box, color: '#999' }}>{item.n}. {item.q} — waiting to be asked…</div>;
  }
  return (
    <div style={{ ...box, borderLeft: `5px solid ${item.mark ? MARK_COLOUR[item.mark] : '#ddd'}` }}>
      <h3 style={{ margin: '0 0 0.25rem', fontSize: '1.05rem' }}>{item.n}. {item.q}</h3>
      <div style={{ color: '#888', fontSize: '0.85rem' }}>
        {item.standalone && item.standalone !== item.q && <>Understood as: <em>{item.standalone}</em> • </>}
        {item.seconds} s
        {item.should_say && <> • Should say: {item.should_say}</>}
      </div>
      <div style={{ margin: '0.75rem 0', color: '#333', lineHeight: 1.55 }}>
        {item.answer_error
          ? <p style={{ color: '#c0392b' }}>{item.answer_error}</p>
          : renderAnswer(item.answer || '(no answer)', false)}
        {item.fallback && <p style={{ color: '#a0522d' }}>(Hidden on the page: too few citations.)</p>}
      </div>
      {item.sources && item.sources.length > 0 && (
        <details style={{ color: '#999', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          <summary>Sources</summary>
          {item.sources.map((s, i) => <div key={i}>[{i + 1}] {s}</div>)}
        </details>
      )}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        {['Right', 'Partly', 'Wrong'].map(m => (
          <button key={m} onClick={() => save(item.mark === m ? null : m, note)}
            style={{ padding: '0.45rem 1rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.95rem',
              border: `2px solid ${item.mark === m ? MARK_COLOUR[m] : '#ddd'}`,
              background: item.mark === m ? MARK_COLOUR[m] : 'white', color: item.mark === m ? 'white' : '#333' }}>
            {m === 'Partly' ? 'Partly right' : m}
          </button>
        ))}
        {item.note_file && <span style={{ color: '#2e8b57', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><CheckCircle2 size={15} /> note saved</span>}
      </div>
      {item.mark && item.mark !== 'Right' && (
        <div style={{ marginTop: '0.6rem', display: 'grid', gap: '0.5rem' }}>
          <textarea value={note} onChange={e => setNote(e.target.value)} onBlur={() => note !== (item.note || '') && save(item.mark, note)}
            placeholder="What is wrong or missing, in your own words" rows={3} style={{ ...input, resize: 'vertical' }} />
          <div>
            <button onClick={draft} disabled={!note.trim() || drafting}
              style={{ padding: '0.45rem 1rem', background: '#2e8b57', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer',
                opacity: !note.trim() || drafting ? 0.6 : 1 }}>
              {drafting ? 'Drafting…' : item.note_file ? 'Draft another note' : 'Draft a note from this'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Test questions, runs of them, marking, and notes drafted from corrections, all on the local model.
export function ImprovePanel() {
  const queryClient = useQueryClient();
  const runs = useQuery('improve-runs', () => axios.get('/api/handouts/eval/runs').then(r => r.data as { runs: RunSummary[]; running: boolean }),
    { refetchInterval: (d: any) => (d?.running ? 5000 : false) });
  const [selected, setSelected] = useState<string | null>(null);
  const runId = selected || runs.data?.runs[0]?.id || null;
  const run = useQuery(['improve-run', runId], () => axios.get(`/api/handouts/eval/runs/${runId}`).then(r => r.data),
    { enabled: !!runId, refetchInterval: (d: any) => (d?.status === 'running' ? 5000 : false) });
  const [check, setCheck] = useState<{ hits: number; total: number } | null>(null);
  const [draft, setDraft] = useState<{ item: RunItem; note: NoteDraft } | null>(null);
  const [message, setMessage] = useState('');

  const start = async () => {
    const { data } = await axios.post('/api/handouts/eval/runs', {});
    if (data.started) setSelected(data.id);
    else setMessage(data.reason);
    queryClient.invalidateQueries('improve-runs');
  };
  const searchCheck = async () => setCheck((await axios.get('/api/handouts/eval/search-check')).data);
  const openDraft = async (item: RunItem) => {
    try {
      const { data } = await axios.post(`/api/handouts/eval/runs/${runId}/items/${item.n}/draft-note`);
      setDraft({ item, note: { topic: data.topic, body: data.body, entities: data.entities, corrects: null } });
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Could not draft the note.');
    }
  };
  const summary: RunSummary | undefined = run.data?.summary;

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <p style={{ margin: 0, color: '#666' }}>
        Run your test questions, mark each answer, and turn corrections into teacher notes. Everything here runs on your local Qwen.
      </p>
      <TestQuestions />
      <div style={{ ...box, display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <button onClick={start} disabled={runs.data?.running}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.6rem 1.2rem', background: '#667eea', color: 'white',
            border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 500, opacity: runs.data?.running ? 0.6 : 1 }}>
          <Play size={16} /> {runs.data?.running ? 'Running…' : 'Run all questions'}
        </button>
        <span style={{ color: '#888', fontSize: '0.85rem' }}>About half a minute per question; answers on the page are slower while it runs.</span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {check && <span style={{ color: check.hits === check.total ? '#2e8b57' : '#c98a00' }}>Search check: {check.hits}/{check.total}</span>}
          <button onClick={searchCheck} title="Do the questions find an expected handout? A few seconds, no Qwen"
            style={{ padding: '0.4rem 0.9rem', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
            Search check
          </button>
        </span>
      </div>
      {message && <div style={{ ...box, color: '#a0522d' }}>{message}</div>}
      {(runs.data?.runs.length ?? 0) > 0 && (
        <div style={{ ...box, display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ fontWeight: 600 }}>Run</label>
          <select value={runId || ''} onChange={e => setSelected(e.target.value)} style={{ ...input, width: 'auto' }}>
            {runs.data!.runs.map((r: RunSummary) => (
              <option key={r.id} value={r.id}>
                {when(r.started)} — {r.status === 'running' ? `running, ${r.answered} of ${r.total}` : `${r.Right} right, ${r.Partly} partly, ${r.Wrong} wrong, ${r.unmarked} unmarked`}
              </option>
            ))}
          </select>
          {summary && (
            <span style={{ color: '#666' }}>
              {summary.status === 'running' ? `Answering ${summary.answered + 1} of ${summary.total}… ` : ''}
              {summary.average_seconds !== null && `about ${summary.average_seconds} s per answer`}
              {summary.status === 'failed' && <span style={{ color: '#c0392b' }}> • stopped early (is LM Studio running?)</span>}
            </span>
          )}
        </div>
      )}
      {(run.data?.items || []).map((item: RunItem) => <RunItemCard key={`${runId}-${item.n}`} runId={runId!} item={item} onDraft={openDraft} />)}
      {draft && (
        <NoteEditor draft={draft.note} onClose={() => setDraft(null)}
          onSaved={async note => {
            await axios.post(`/api/handouts/eval/runs/${runId}/items/${draft.item.n}/note-saved`, { file: note.file });
            setDraft(null);
            setMessage(`Note saved: "${note.topic}". Answers use it from now on.`);
            queryClient.invalidateQueries(['improve-run', runId]);
            queryClient.invalidateQueries('handouts-notes');
          }} />
      )}
    </div>
  );
}

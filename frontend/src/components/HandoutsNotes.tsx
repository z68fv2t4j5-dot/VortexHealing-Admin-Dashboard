import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { StickyNote } from 'lucide-react';

export interface Note {
  file: string;
  date: string | null;
  topic: string;
  entities: string[];
  corrects: string | null;
  body: string;
}

export interface NoteDraft {
  topic: string;
  body: string;
  entities: string[];
  corrects: string | null;
  file?: string;  // set when editing an existing note
}

const label = { display: 'block', fontWeight: 600, marginBottom: '0.4rem', color: '#333' } as const;
const field = { width: '100%', padding: '0.6rem 0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.95rem',
  boxSizing: 'border-box' } as const;

// Write or edit a teacher note. `sources` offers the handouts an answer cited, for "Corrects".
export function NoteEditor({ draft, sources = [], onClose, onSaved }: {
  draft: NoteDraft; sources?: string[]; onClose: () => void; onSaved: (note: Note) => void;
}) {
  const [topic, setTopic] = useState(draft.topic);
  const [body, setBody] = useState(draft.body);
  const [entities, setEntities] = useState(draft.entities.join(', '));
  const [corrects, setCorrects] = useState(draft.corrects || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const save = async () => {
    setSaving(true);
    setError('');
    const payload = { topic, body, corrects: corrects || null,
      entities: entities.split(',').map(e => e.trim()).filter(Boolean) };
    try {
      const { data } = draft.file
        ? await axios.put(`/api/handouts/notes/${draft.file}`, payload)
        : await axios.post('/api/handouts/notes', payload);
      onSaved(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'The note could not be saved. Is the backend running?');
      setSaving(false);
    }
  };

  return (
    <div onClick={() => !saving && onClose()}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div onClick={e => e.stopPropagation()}
        style={{ background: 'white', borderRadius: '12px', padding: '2rem', maxWidth: '640px', width: '90%',
          maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <StickyNote size={24} style={{ color: '#2e8b57' }} /> {draft.file ? 'Edit teacher note' : 'Teacher note'}
          </h2>
          <button onClick={onClose} disabled={saving}
            style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#999' }}>×</button>
        </div>
        <p style={{ margin: '0 0 1.25rem', color: '#666', fontSize: '0.9rem' }}>
          Answers use your notes from now on, cite them as "Teacher note", and follow them where the handouts disagree.
        </p>
        <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={label}>Topic</label>
            <input value={topic} onChange={e => setTopic(e.target.value)} disabled={saving} style={field} />
          </div>
          <div>
            <label style={label}>Note</label>
            <textarea value={body} onChange={e => setBody(e.target.value)} disabled={saving} rows={7} autoFocus
              placeholder="What the handouts miss, get wrong, or how you teach it…" style={{ ...field, resize: 'vertical' }} />
          </div>
          <div>
            <label style={label}>About <span style={{ fontWeight: 400, color: '#999' }}>(names, separated by commas; the note shows on their cards)</span></label>
            <input value={entities} onChange={e => setEntities(e.target.value)} disabled={saving} style={field} />
          </div>
          <div>
            <label style={label}>Corrects <span style={{ fontWeight: 400, color: '#999' }}>(optional)</span></label>
            <input value={corrects} onChange={e => setCorrects(e.target.value)} disabled={saving} list="note-sources"
              placeholder="A handout this note corrects" style={field} />
            <datalist id="note-sources">{sources.map(s => <option key={s} value={s} />)}</datalist>
          </div>
        </div>
        {error && <p style={{ color: '#c0392b', marginTop: 0 }}>{error}</p>}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button onClick={onClose} disabled={saving}
            style={{ padding: '0.65rem 1.25rem', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
            Cancel
          </button>
          <button onClick={save} disabled={saving || !topic.trim() || !body.trim()}
            style={{ padding: '0.65rem 1.25rem', background: '#2e8b57', color: 'white', border: 'none', borderRadius: '6px',
              cursor: 'pointer', fontWeight: 500, opacity: saving || !topic.trim() || !body.trim() ? 0.6 : 1 }}>
            {saving ? 'Saving…' : 'Save note'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Every teacher note, newest first, with edit and delete.
export function NotesList() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery('handouts-notes', () => axios.get('/api/handouts/notes').then(r => r.data.notes as Note[]));
  const [editing, setEditing] = useState<NoteDraft | null>(null);
  const refresh = () => { queryClient.invalidateQueries('handouts-notes'); queryClient.invalidateQueries('handouts-status'); };

  const remove = async (note: Note) => {
    if (!window.confirm(`Delete the note "${note.topic || note.file}"? Answers will stop using it.`)) return;
    await axios.delete(`/api/handouts/notes/${note.file}`).catch(() => null);
    refresh();
  };

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p style={{ margin: 0, color: '#666' }}>
          Your notes are kept as files in the Handouts-KB/notes folder; editing them there works too.
        </p>
        <button onClick={() => setEditing({ topic: '', body: '', entities: [], corrects: null })}
          style={{ padding: '0.6rem 1.1rem', background: '#2e8b57', color: 'white', border: 'none', borderRadius: '6px',
            cursor: 'pointer', fontWeight: 500, whiteSpace: 'nowrap' }}>
          New note
        </button>
      </div>
      {isLoading && <p style={{ color: '#999' }}>Loading…</p>}
      {data && data.length === 0 && <p style={{ color: '#999' }}>No notes yet.</p>}
      {(data || []).map(n => (
        <div key={n.file} style={{ background: 'white', padding: '1.25rem 1.5rem', borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)', borderLeft: '4px solid #2e8b57' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'baseline' }}>
            <h3 style={{ margin: 0, fontSize: '1.05rem' }}>{n.topic || n.file}</h3>
            <span style={{ display: 'flex', gap: '0.75rem', fontSize: '0.85rem' }}>
              <button onClick={() => setEditing({ ...n, file: n.file })}
                style={{ background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', padding: 0 }}>Edit</button>
              <button onClick={() => remove(n)}
                style={{ background: 'none', border: 'none', color: '#c0392b', cursor: 'pointer', padding: 0 }}>Delete</button>
            </span>
          </div>
          <p style={{ margin: '0.25rem 0 0.5rem', fontSize: '0.8rem', color: '#999' }}>
            {n.date || 'undated'}
            {n.entities.length > 0 && ` • about ${n.entities.join(', ')}`}
            {n.corrects && ` • corrects ${n.corrects}`}
          </p>
          <p style={{ margin: 0, color: '#444', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{n.body}</p>
        </div>
      ))}
      {editing && <NoteEditor draft={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); refresh(); }} />}
    </div>
  );
}

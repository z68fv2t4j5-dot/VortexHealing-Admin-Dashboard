import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { Download, Upload } from 'lucide-react';
import '../styles/Pages.css';

// One row of the review table: what /api/class-lists/preview suggests, plus Daniel's Remove tick
interface Attendee {
  first: string;
  last: string;
  email: string;
  phone: string;
  address: string;
  repeater: boolean;
  reason: string;
  check: boolean;
  address_misses: string[];
  remove?: boolean;
}

interface ScheduledClass {
  id: number;
  name: string;
  start_date: string | null;
}

const cell: React.CSSProperties = { padding: '0.6rem 0.75rem', borderBottom: '1px solid #eee', verticalAlign: 'top' };
const head: React.CSSProperties = { ...cell, textAlign: 'left', fontWeight: 600, color: '#333', background: '#f5f5f5' };
const box: React.CSSProperties = { background: 'white', borderRadius: '8px', padding: '1.25rem', marginBottom: '1.25rem',
  boxShadow: '0 2px 4px rgba(0,0,0,0.05)' };
const input: React.CSSProperties = { padding: '0.6rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem',
  width: '100%', boxSizing: 'border-box' };

const errorText = async (error: any, fallback: string) => {
  const data = error?.response?.data;
  try {
    const body = data instanceof Blob ? JSON.parse(await data.text()) : data;
    return body?.detail || fallback;
  } catch {
    return fallback;
  }
};

export default function ClassLists() {
  const [classId, setClassId] = useState('');
  const [file, setFile] = useState<{ name: string; text: string } | null>(null);
  const [title, setTitle] = useState('');
  const [format, setFormat] = useState<'standard' | 'foundational'>('standard');
  const [attendees, setAttendees] = useState<Attendee[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const { data: classes = [] } = useQuery<ScheduledClass[]>('classes', () =>
    axios.get('/api/classes/').then(r => r.data).catch(() => [])
  );
  // Classes from a month ago onwards, soonest first: lists are made shortly before a class
  const monthAgo = Date.now() - 30 * 24 * 3600 * 1000;
  const pickable = classes
    .filter(c => c.start_date && new Date(c.start_date).getTime() >= monthAgo)
    .sort((a, b) => (a.start_date! < b.start_date! ? -1 : 1));

  // A new file or class asks the backend again; the title, format and ticks start from its suggestions
  useEffect(() => {
    if (!file) return;
    setBusy(true);
    setError('');
    axios.post('/api/class-lists/preview', {
      filename: file.name, csv_text: file.text, class_id: classId ? Number(classId) : null
    })
      .then(r => {
        setTitle(r.data.title);
        setFormat(r.data.format);
        setAttendees(r.data.attendees);
      })
      .catch(async e => {
        setAttendees([]);
        setError(await errorText(e, 'Could not read the file. Is the backend running?'));
      })
      .finally(() => setBusy(false));
  }, [file, classId]);

  const chooseFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile({ name: f.name, text: await f.text() });
    e.target.value = '';  // choosing the same file again still triggers a change
  };

  const tick = (i: number, field: 'repeater' | 'remove') =>
    setAttendees(list => list.map((a, j) => (j === i ? { ...a, [field]: !a[field] } : a)));

  const kept = attendees.filter(a => !a.remove);
  const repeaters = kept.filter(a => a.repeater).length;

  const download = async () => {
    setBusy(true);
    setError('');
    try {
      const r = await axios.post('/api/class-lists/build', {
        title, format,
        attendees: kept.map(({ first, last, email, phone, address, repeater }) =>
          ({ first, last, email, phone, address, repeater }))
      }, { responseType: 'blob' });
      const url = URL.createObjectURL(r.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title.trim().replace(/[\\/:*?"<>|]/g, '-')}.xlsx`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);  // Safari drops a download whose URL is revoked at once
    } catch (e) {
      setError(await errorText(e, 'Could not make the class list. Is the backend running?'));
    } finally {
      setBusy(false);
    }
  };

  const note = (a: Attendee) => (
    <>
      {a.repeater && a.reason && (
        <div style={{ color: a.check ? '#c05621' : '#666' }}>
          {a.reason}{a.check ? ': not a repeater coupon, check' : ''}
        </div>
      )}
      {format === 'foundational' && !a.repeater && a.address_misses.length > 0 && (
        <div style={{ color: '#c05621' }}>Address: {a.address_misses.join(', ')}</div>
      )}
    </>
  );

  return (
    <div className="page">
      <h1 style={{ marginBottom: '0.5rem' }}>Class Lists</h1>
      <p style={{ color: '#666', marginTop: 0, marginBottom: '1.5rem' }}>
        Upload a Corsizio attendee export, check who is a repeater, and download the class list.
        Nothing you upload is saved.
      </p>

      <div style={box}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ flex: '1 1 260px' }}>
            <div style={{ fontWeight: 500, marginBottom: '0.35rem' }}>Class</div>
            <select value={classId} onChange={e => setClassId(e.target.value)} style={input}>
              <option value="">Not on the schedule (title from the file name)</option>
              {pickable.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name}, {new Date(c.start_date!).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}
                </option>
              ))}
            </select>
          </label>
          <label style={{
            padding: '0.65rem 1.25rem', background: '#667eea', color: 'white', borderRadius: '8px', cursor: 'pointer',
            fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.5rem'
          }}>
            <Upload size={18} /> {file ? 'Choose another file' : 'Choose CSV file'}
            <input type="file" accept=".csv,text/csv" onChange={chooseFile} style={{ display: 'none' }} />
          </label>
        </div>
        {file && (
          <p style={{ margin: '0.75rem 0 0', color: '#666' }}>
            File: {file.name}. Changing the class or the file starts the review again.
          </p>
        )}
      </div>

      {error && (
        <div style={{ ...box, background: '#fff5f5', color: '#c53030' }}>{error}</div>
      )}

      {attendees.length > 0 && (
        <>
          <div style={box}>
            <label>
              <div style={{ fontWeight: 500, marginBottom: '0.35rem' }}>Title</div>
              <input value={title} onChange={e => setTitle(e.target.value)} style={input}
                placeholder="Sensing I Class List October 3 2026 Daniel" />
            </label>
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginTop: '1rem' }}>
              <label><input type="radio" checked={format === 'standard'} onChange={() => setFormat('standard')} /> Standard</label>
              <label><input type="radio" checked={format === 'foundational'} onChange={() => setFormat('foundational')} /> Foundational (phone and address)</label>
            </div>
          </div>

          <div style={{ background: 'white', borderRadius: '8px', overflowX: 'auto', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', marginBottom: '1.25rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={head}>Name</th>
                  <th style={head}>Email</th>
                  <th style={{ ...head, textAlign: 'center' }}>Repeater</th>
                  <th style={{ ...head, textAlign: 'center' }}>Remove</th>
                  <th style={head}>Note</th>
                </tr>
              </thead>
              <tbody>
                {attendees.map((a, i) => (
                  <tr key={i} style={{ opacity: a.remove ? 0.4 : 1, background: a.repeater ? '#fffbea' : 'white' }}>
                    <td style={{ ...cell, whiteSpace: 'nowrap', textDecoration: a.remove ? 'line-through' : 'none' }}>
                      {a.last}, {a.first}
                    </td>
                    <td style={cell}>{a.email}</td>
                    <td style={{ ...cell, textAlign: 'center' }}>
                      <input type="checkbox" checked={a.repeater} onChange={() => tick(i, 'repeater')} aria-label={`${a.first} ${a.last} is a repeater`} />
                    </td>
                    <td style={{ ...cell, textAlign: 'center' }}>
                      <input type="checkbox" checked={!!a.remove} onChange={() => tick(i, 'remove')} aria-label={`Remove ${a.first} ${a.last}`} />
                    </td>
                    <td style={{ ...cell, fontSize: '0.9rem' }}>{note(a)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <span style={{ color: '#666' }}>
              {kept.length - repeaters} in the main list, {repeaters} repeater{repeaters === 1 ? '' : 's'}
              {attendees.length > kept.length ? `, ${attendees.length - kept.length} removed` : ''}
            </span>
            <button onClick={download} disabled={busy || !title.trim() || kept.length === 0} style={{
              padding: '0.75rem 1.5rem', background: busy || !title.trim() || kept.length === 0 ? '#a3b0f0' : '#667eea',
              color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 500,
              display: 'flex', alignItems: 'center', gap: '0.5rem'
            }}>
              <Download size={18} /> {busy ? 'Working...' : 'Download class list'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { ClipboardCheck, Check } from 'lucide-react';

interface AdminTask {
  key: string;
  title: string;
  due: string;
  days_late: number;
}

const formatDate = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' });

// Tasks worked out from the class schedule and the quarter; the daily digest lists the same ones (ADR-0010)
export default function AdminTasksDue() {
  const [ticking, setTicking] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: due = [], isLoading } = useQuery<AdminTask[]>('adminTasks', () =>
    axios.get('/api/admin-tasks').then(r => r.data).catch(() => [])
  );

  const handleDone = async (t: AdminTask) => {
    setTicking(t.key);
    try {
      await axios.post('/api/admin-tasks/done', { key: t.key });
      queryClient.invalidateQueries('adminTasks');
    } catch (error: any) {
      console.error('Error marking task done:', error);
      alert(error?.response?.data?.detail || 'Error marking the task done. Is the backend running?');
    } finally {
      setTicking(null);
    }
  };

  if (isLoading) return null;

  return (
    <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
      <h2 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem' }}>
        <ClipboardCheck size={20} style={{ color: '#667eea' }} /> From your classes
      </h2>

      {due.length === 0 ? (
        <p style={{ margin: 0, color: '#999' }}>No class or quarterly tasks are due in the next 7 days.</p>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {due.map(t => (
            <div
              key={t.key}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', border: '1px solid #e0e0e0', borderRadius: '8px', padding: '1rem' }}
            >
              <div>
                <div style={{ fontWeight: 600, color: '#333' }}>{t.title}</div>
                <div style={{ color: t.days_late > 0 ? '#c0392b' : '#666', fontSize: '0.9rem' }}>
                  {t.days_late > 0
                    ? `Overdue: due ${formatDate(t.due)} (${t.days_late} day${t.days_late === 1 ? '' : 's'} ago)`
                    : t.days_late === 0 ? 'Due today' : `Due ${formatDate(t.due)}`}
                </div>
              </div>
              <button
                onClick={() => handleDone(t)}
                disabled={ticking !== null}
                style={{ padding: '0.5rem 1rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '8px', cursor: ticking ? 'not-allowed' : 'pointer', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: ticking === t.key ? 0.6 : 1 }}
              >
                <Check size={16} /> {ticking === t.key ? 'Saving…' : 'Done'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

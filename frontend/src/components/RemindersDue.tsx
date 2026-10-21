import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { Bell, Send } from 'lucide-react';

interface DueReminder {
  class_id: number;
  class_name: string;
  class_date: string;
  stage: string;
  label: string;
  reminder_date: string;
  days_late: number;
  recipient_count: number;
  sample_recipients: string[];
  subject: string;
  body: string;
}

const formatDate = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.75rem',
  border: '1px solid #ddd',
  borderRadius: '6px',
  fontSize: '1rem',
  fontFamily: 'inherit',
  boxSizing: 'border-box'
};

const buttonStyle = (primary: boolean, disabled = false): React.CSSProperties => ({
  flex: 1,
  padding: '0.75rem 1.5rem',
  background: primary ? '#667eea' : '#f0f0f0',
  color: primary ? 'white' : '#333',
  border: 'none',
  borderRadius: '8px',
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontWeight: '500',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '0.5rem',
  opacity: disabled ? 0.6 : 1
});

// Reminders whose date has arrived; a person reviews each one and approves it (ADR-0007)
export default function RemindersDue() {
  const [reviewing, setReviewing] = useState<DueReminder | null>(null);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [approving, setApproving] = useState(false);
  const queryClient = useQueryClient();

  const { data: due = [], isLoading } = useQuery<DueReminder[]>('remindersDue', () =>
    axios.get('/api/reminders/due').then(r => r.data).catch(() => [])
  );

  const openReview = (r: DueReminder) => {
    setReviewing(r);
    setSubject(r.subject);
    setBody(r.body);
  };

  const handleApprove = async () => {
    if (!reviewing) return;
    setApproving(true);
    try {
      const response = await axios.post('/api/reminders/approve', {
        class_id: reviewing.class_id,
        stage: reviewing.stage,
        subject,
        body
      });
      queryClient.invalidateQueries('remindersDue');
      queryClient.invalidateQueries('campaigns');
      alert(`✓ ${response.data.message}`);
      setReviewing(null);
    } catch (error: any) {
      console.error('Error approving reminder:', error);
      alert(error?.response?.data?.detail || 'Error approving reminder. Is the backend running on localhost:8000?');
    } finally {
      setApproving(false);
    }
  };

  if (isLoading) return null;

  return (
    <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
      <h2 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem' }}>
        <Bell size={20} style={{ color: '#667eea' }} /> Reminders due
      </h2>

      {due.length === 0 ? (
        <p style={{ margin: 0, color: '#999' }}>No class reminders are due.</p>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {due.map(r => (
            <div
              key={`${r.class_id}-${r.stage}`}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', border: '1px solid #e0e0e0', borderRadius: '8px', padding: '1rem' }}
            >
              <div>
                <div style={{ fontWeight: 600, color: '#333' }}>{r.class_name}</div>
                <div style={{ color: '#666', fontSize: '0.9rem' }}>
                  {r.label} · class starts {formatDate(r.class_date)} · {r.recipient_count} eligible APAC Wizards
                </div>
                {r.days_late > 0 && (
                  <div style={{ color: '#856404', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                    Due {formatDate(r.reminder_date)} ({r.days_late} day{r.days_late === 1 ? '' : 's'} ago); drops off after 7 days
                  </div>
                )}
              </div>
              <button onClick={() => openReview(r)} style={{ ...buttonStyle(true), flex: 'none' }}>
                Review
              </button>
            </div>
          ))}
        </div>
      )}

      {reviewing && (
        <div
          onClick={() => !approving && setReviewing(null)}
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ background: 'white', borderRadius: '12px', padding: '2rem', maxWidth: '600px', width: '90%', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}
          >
            <h2 style={{ margin: '0 0 0.25rem' }}>{reviewing.class_name}</h2>
            <p style={{ margin: '0 0 1.5rem', color: '#666' }}>
              {reviewing.label} · class starts {formatDate(reviewing.class_date)}
            </p>

            <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem', color: '#333' }}>Subject</label>
                <input value={subject} onChange={(e) => setSubject(e.target.value)} disabled={approving} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem', color: '#333' }}>Body</label>
                <textarea value={body} onChange={(e) => setBody(e.target.value)} disabled={approving} style={{ ...inputStyle, resize: 'vertical', minHeight: '180px' }} />
              </div>
              <div style={{ background: '#f9f9f9', borderRadius: '6px', padding: '0.75rem' }}>
                <strong style={{ color: '#333' }}>{reviewing.recipient_count} eligible APAC Wizards</strong>
                <span style={{ color: '#666' }}> who have not done this class, including:</span>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0.5rem 0 0' }}>
                  {reviewing.sample_recipients.map(name => (
                    <li key={name} style={{ padding: '0.25rem 0', color: '#666', fontSize: '0.9rem' }}>{name}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={handleApprove}
                disabled={approving || !subject.trim() || !body.trim() || reviewing.recipient_count === 0}
                style={buttonStyle(true, approving || !subject.trim() || !body.trim() || reviewing.recipient_count === 0)}
              >
                <Send size={18} /> {approving ? 'Recording…' : 'Approve & send'}
              </button>
              <button onClick={() => setReviewing(null)} disabled={approving} style={buttonStyle(false, approving)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { Mail, Send, Filter, Tag, X } from 'lucide-react';
import '../styles/Pages.css';
import RemindersDue from '../components/RemindersDue';

interface Campaign {
  id: number;
  title: string;
  subject: string;
  body: string;
  recipient_tags: string;
  recipient_lists: string;
  recipient_count: number;
  status: string;
  created_at: string;
}

interface PreviewResult {
  total_recipients: number;
  sample_count: number;
  sample_recipients: { id: number; name: string; email: string }[];
}

// What the send confirmation modal is about to send. campaignId is set when
// sending an existing draft; otherwise the campaign is created first.
interface PendingSend {
  campaignId?: number;
  title: string;
  subject: string;
  body: string;
  recipient_tags: string;
  recipient_lists: string;
}

interface EmailOptions {
  lists: string[];
  tags: string[];
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(0,0,0,0.5)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000
};

const modalStyle: React.CSSProperties = {
  background: 'white',
  borderRadius: '12px',
  padding: '2rem',
  maxWidth: '600px',
  width: '90%',
  maxHeight: '90vh',
  overflowY: 'auto',
  boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontWeight: '600',
  marginBottom: '0.5rem',
  color: '#333'
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.75rem',
  border: '1px solid #ddd',
  borderRadius: '6px',
  fontSize: '1rem',
  fontFamily: 'inherit',
  boxSizing: 'border-box'
};

const primaryButton = (disabled = false): React.CSSProperties => ({
  flex: 1,
  padding: '0.75rem 1.5rem',
  background: '#667eea',
  color: 'white',
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

const secondaryButton = (disabled = false): React.CSSProperties => ({
  ...primaryButton(disabled),
  background: '#f0f0f0',
  color: '#333'
});

const closeButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  color: '#999'
};

const statusBadge = (status: string): React.CSSProperties => ({
  background: status === 'sent' ? '#d4edda' : status === 'failed' ? '#f8d7da' : '#fff3cd',
  color: status === 'sent' ? '#155724' : status === 'failed' ? '#721c24' : '#856404',
  padding: '0.25rem 0.75rem',
  borderRadius: '4px',
  fontSize: '0.85rem'
});

const chipStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.25rem',
  background: '#eef0fc',
  color: '#667eea',
  padding: '0.25rem 0.5rem',
  borderRadius: '4px',
  fontSize: '0.85rem'
};

function RecipientSample({ preview }: { preview: PreviewResult }) {
  return (
    <ul style={{ listStyle: 'none', padding: 0, margin: '0.5rem 0 0' }}>
      {preview.sample_recipients.map(r => (
        <li key={r.id} style={{ padding: '0.25rem 0', color: '#666', fontSize: '0.9rem' }}>
          {r.name} &lt;{r.email}&gt;
        </li>
      ))}
    </ul>
  );
}

export default function Email() {
  const [showComposer, setShowComposer] = useState(false);
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const [pendingSend, setPendingSend] = useState<PendingSend | null>(null);
  const [confirmPreview, setConfirmPreview] = useState<PreviewResult | null>(null);
  const [sending, setSending] = useState(false);

  const [viewing, setViewing] = useState<Campaign | null>(null);
  const queryClient = useQueryClient();

  const { data: campaigns = [], isLoading } = useQuery<Campaign[]>('campaigns', () =>
    axios.get('/api/email/campaigns').then(r => r.data).catch(() => [])
  );

  // The backend decides the scope: the APAC Wizards list and full-word class tags
  const { data: options } = useQuery<EmailOptions>('emailOptions', () =>
    axios.get('/api/email/options').then(r => r.data)
  );
  const tagOptions = options?.tags ?? [];

  const recipientTags = selectedTags.join(',');
  // Empty would mean every student, so nothing can be previewed or sent until the list has loaded
  const recipientLists = (options?.lists ?? []).join(',');

  // Live recipient count while composing
  const { data: composerPreview, isFetching: previewLoading } = useQuery<PreviewResult>(
    ['emailPreview', recipientTags, recipientLists],
    () =>
      axios.post('/api/email/preview', {
        title, subject, body,
        recipient_tags: recipientTags,
        recipient_lists: recipientLists
      }).then(r => r.data),
    { enabled: showComposer && !!recipientLists, keepPreviousData: true }
  );

  const resetComposer = () => {
    setTitle('');
    setSubject('');
    setBody('');
    setSelectedTags([]);
    setShowComposer(false);
  };

  const composerIncomplete = !title.trim() || !subject.trim() || !body.trim() || !recipientLists;

  const handleSaveDraft = async () => {
    if (composerIncomplete) return;
    setSaving(true);
    try {
      await axios.post('/api/email/campaigns', {
        title, subject, body,
        recipient_tags: recipientTags,
        recipient_lists: recipientLists
      });
      queryClient.invalidateQueries('campaigns');
      resetComposer();
    } catch (error) {
      console.error('Error saving draft:', error);
      alert('Error saving draft. Is the backend running?');
    } finally {
      setSaving(false);
    }
  };

  const openConfirm = async (send: PendingSend) => {
    setPendingSend(send);
    setConfirmPreview(null);
    try {
      const response = await axios.post('/api/email/preview', send);
      setConfirmPreview(response.data);
    } catch (error) {
      console.error('Error loading preview:', error);
      alert('Error loading recipients. Is the backend running?');
      setPendingSend(null);
    }
  };

  const handleSendNow = async () => {
    if (!pendingSend) return;
    setSending(true);
    try {
      let campaignId = pendingSend.campaignId;
      if (campaignId === undefined) {
        const { campaignId: _, ...campaign } = pendingSend;
        const created = await axios.post('/api/email/campaigns', campaign);
        campaignId = created.data.id;
      }
      // campaign_id is a query parameter on this endpoint, not a JSON body field
      const response = await axios.post('/api/email/send', null, { params: { campaign_id: campaignId } });
      if (response.data.error) throw new Error(response.data.error);

      queryClient.invalidateQueries('campaigns');
      alert(`✓ ${response.data.message}`);
      setPendingSend(null);
      setViewing(null);
      if (pendingSend.campaignId === undefined) resetComposer();
    } catch (error) {
      console.error('Error sending campaign:', error);
      alert('Error sending campaign. Is the backend running?');
    } finally {
      setSending(false);
    }
  };

  const addOption = (value: string, selected: string[], setSelected: (v: string[]) => void) => {
    if (value && !selected.includes(value)) setSelected([...selected, value]);
  };

  const removeOption = (value: string, selected: string[], setSelected: (v: string[]) => void) =>
    setSelected(selected.filter(v => v !== value));

  if (isLoading) return <div className="loading">Loading campaigns...</div>;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', gap: '1rem', flexWrap: 'wrap' }}>
        <h1>Email Campaigns</h1>
        <button onClick={() => setShowComposer(true)} style={{ ...primaryButton(), flex: 'none' }}>
          <Mail size={18} /> New Campaign
        </button>
      </div>

      <RemindersDue />

      {campaigns.length === 0 ? (
        <div style={{
          background: 'white',
          padding: '2rem',
          textAlign: 'center',
          borderRadius: '8px',
          color: '#999'
        }}>
          <p>No campaigns yet. Create one with the New Campaign button above.</p>
        </div>
      ) : (
        <div style={{ background: 'white', borderRadius: '8px', overflowX: 'auto', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #e0e0e0' }}>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Title</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Subject</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Recipients</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Status</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map(c => (
                <tr
                  key={c.id}
                  onClick={() => setViewing(c)}
                  style={{ borderBottom: '1px solid #e0e0e0', cursor: 'pointer' }}
                >
                  <td style={{ padding: '1rem', color: '#333' }}>{c.title}</td>
                  <td style={{ padding: '1rem', color: '#666' }}>{c.subject}</td>
                  <td style={{ padding: '1rem', color: '#666' }}>{c.recipient_count}</td>
                  <td style={{ padding: '1rem', color: '#666' }}>
                    <span style={statusBadge(c.status)}>{c.status}</span>
                  </td>
                  <td style={{ padding: '1rem', color: '#666' }}>{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Campaign Composer Modal */}
      {showComposer && (
        <div onClick={() => !saving && setShowComposer(false)} style={overlayStyle}>
          <div onClick={(e) => e.stopPropagation()} style={modalStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Mail size={24} style={{ color: '#667eea' }} /> New Campaign
              </h2>
              <button onClick={() => setShowComposer(false)} disabled={saving} style={{ ...closeButtonStyle, fontSize: '1.5rem' }}>
                ×
              </button>
            </div>

            <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={labelStyle}>Title</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Internal name, e.g. Magical Structures – 1 month reminder"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Subject</label>
                <input
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="What students see in their inbox"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Body</label>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  style={{ ...inputStyle, resize: 'vertical', minHeight: '140px' }}
                />
              </div>

              <div>
                <label style={{ ...labelStyle, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Filter size={16} style={{ color: '#667eea' }} /> Recipients
                </label>
                <p style={{ margin: '0 0 0.5rem', color: '#666', fontSize: '0.9rem' }}>
                  List: <strong>{recipientLists || 'loading…'}</strong>
                </p>
                <select
                  value=""
                  onChange={(e) => addOption(e.target.value, selectedTags, setSelectedTags)}
                  style={inputStyle}
                >
                  <option value="">Add class tag…</option>
                  {tagOptions.map(t => <option key={t} value={t}>{t}</option>)}
                </select>

                {selectedTags.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                    {selectedTags.map(t => (
                      <span key={`tag-${t}`} style={chipStyle}>
                        <Tag size={12} /> {t}
                        <button onClick={() => removeOption(t, selectedTags, setSelectedTags)} style={{ ...closeButtonStyle, padding: 0, display: 'flex' }}>
                          <X size={12} />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                <div style={{ background: '#f9f9f9', borderRadius: '6px', padding: '0.75rem', marginTop: '0.75rem' }}>
                  {composerPreview ? (
                    <>
                      <strong style={{ color: '#333', opacity: previewLoading ? 0.6 : 1 }}>
                        {composerPreview.total_recipients} students match your filters
                      </strong>
                      {selectedTags.length === 0 && (
                        <div style={{ color: '#856404', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                          No class tag selected: this will go to every student on {recipientLists}.
                        </div>
                      )}
                      <RecipientSample preview={composerPreview} />
                    </>
                  ) : (
                    <span style={{ color: '#999' }}>Counting recipients…</span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => openConfirm({
                  title, subject, body,
                  recipient_tags: recipientTags,
                  recipient_lists: recipientLists
                })}
                disabled={composerIncomplete || saving}
                style={primaryButton(composerIncomplete || saving)}
              >
                <Send size={18} /> Preview &amp; Send
              </button>
              <button
                onClick={handleSaveDraft}
                disabled={composerIncomplete || saving}
                style={secondaryButton(composerIncomplete || saving)}
              >
                {saving ? 'Saving…' : 'Save as Draft'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Campaign Details Modal */}
      {viewing && (
        <div onClick={() => setViewing(null)} style={overlayStyle}>
          <div onClick={(e) => e.stopPropagation()} style={modalStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>{viewing.title}</h2>
              <button onClick={() => setViewing(null)} style={{ ...closeButtonStyle, fontSize: '1.5rem' }}>×</button>
            </div>
            <p style={{ margin: '0 0 1rem' }}>
              <span style={statusBadge(viewing.status)}>{viewing.status}</span>
              <span style={{ color: '#666', marginLeft: '0.75rem' }}>
                {viewing.recipient_count} recipients · created {new Date(viewing.created_at).toLocaleString()}
              </span>
            </p>
            <p style={{ color: '#666', margin: '0 0 0.25rem' }}>
              <strong>Tags:</strong> {viewing.recipient_tags || 'any'}
            </p>
            <p style={{ color: '#666', margin: '0 0 1rem' }}>
              <strong>Lists:</strong> {viewing.recipient_lists || 'any'}
            </p>
            <p style={{ fontWeight: 600, color: '#333', margin: '0 0 0.5rem' }}>{viewing.subject}</p>
            <div style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9', borderRadius: '6px', padding: '1rem', color: '#333' }}>
              {viewing.body}
            </div>
            {viewing.status === 'draft' && (
              <div style={{ display: 'flex', marginTop: '1.5rem' }}>
                <button
                  onClick={() => openConfirm({
                    campaignId: viewing.id,
                    title: viewing.title,
                    subject: viewing.subject,
                    body: viewing.body,
                    recipient_tags: viewing.recipient_tags,
                    recipient_lists: viewing.recipient_lists
                  })}
                  style={primaryButton()}
                >
                  <Send size={18} /> Send This Draft
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Send Confirmation Modal */}
      {pendingSend && (
        <div onClick={() => !sending && setPendingSend(null)} style={{ ...overlayStyle, zIndex: 1100 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ ...modalStyle, maxWidth: '500px' }}>
            <h2 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Send size={24} style={{ color: '#667eea' }} /> Confirm Send
            </h2>
            {confirmPreview ? (
              <>
                <p style={{ margin: 0, color: '#333' }}>
                  <strong>{pendingSend.subject}</strong> will be sent to{' '}
                  <strong>{confirmPreview.total_recipients}</strong> students, including:
                </p>
                <RecipientSample preview={confirmPreview} />
              </>
            ) : (
              <p style={{ color: '#999' }}>Loading recipients…</p>
            )}
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
              <button
                onClick={handleSendNow}
                disabled={!confirmPreview || sending}
                style={primaryButton(!confirmPreview || sending)}
              >
                {sending ? 'Sending…' : 'Send Now'}
              </button>
              <button
                onClick={() => setPendingSend(null)}
                disabled={sending}
                style={secondaryButton(sending)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

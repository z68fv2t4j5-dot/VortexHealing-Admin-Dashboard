import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { Sparkles, X, Plus, Check } from 'lucide-react';
import AdminTasksDue from '../components/AdminTasksDue';
import '../styles/Pages.css';

export default function Tasks() {
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiPrompt, setAIPrompt] = useState('');
  const [priority, setPriority] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDue, setNewDue] = useState('');
  const [saving, setSaving] = useState(false);
  const queryClient = useQueryClient();

  const { data: tasks = [], isLoading } = useQuery('tasks', () =>
    axios.get(`/api/tasks/`).then(r => r.data).catch(() => [])
  );

  const handleAddTask = async () => {
    if (!newTitle.trim()) return;
    setSaving(true);
    try {
      await axios.post(`/api/tasks/`, {
        title: newTitle.trim(),
        due_date: newDue ? `${newDue}T00:00:00` : null
      });
      queryClient.invalidateQueries('tasks');
      setNewTitle('');
      setNewDue('');
      setShowAddModal(false);
    } catch (error) {
      console.error('Error adding task:', error);
      alert('Error adding the task. Is the backend running?');
    } finally {
      setSaving(false);
    }
  };

  const handleDone = async (id: number) => {
    try {
      await axios.put(`/api/tasks/${id}`, { status: 'done' });
      queryClient.invalidateQueries('tasks');
    } catch (error) {
      console.error('Error marking task done:', error);
      alert('Error marking the task done. Is the backend running?');
    }
  };

  const handleGenerateTask = async () => {
    if (!aiPrompt.trim()) return;

    setGenerating(true);
    try {
      const response = await axios.post(`/api/ai/generate-task`, {
        prompt: aiPrompt,
        priority: priority
      });

      // Refresh tasks list
      queryClient.invalidateQueries('tasks');

      // Show success message
      alert(`✓ Task created: "${response.data.title}"`);

      // Reset form
      setAIPrompt('');
      setPriority(0);
      setShowAIModal(false);
    } catch (error) {
      console.error('Error generating task:', error);
      alert('Error creating task. Make sure Qwen is running at localhost:1234');
    } finally {
      setGenerating(false);
    }
  };

  if (isLoading) return <div className="loading">Loading tasks...</div>;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <h1>Tasks</h1>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => setShowAddModal(true)}
          style={{
            padding: '0.75rem 1.5rem',
            background: '#f0f0f0',
            color: '#333',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Plus size={18} /> Add task
        </button>
        <button
          onClick={() => setShowAIModal(true)}
          style={{
            padding: '0.75rem 1.5rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '500',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Sparkles size={18} /> AI Task
        </button>
        </div>
      </div>

      <AdminTasksDue />

      {tasks.length === 0 ? (
        <div style={{
          background: 'white',
          padding: '2rem',
          textAlign: 'center',
          borderRadius: '8px',
          color: '#999'
        }}>
          <p>No tasks of your own yet. Add one with a due date, and it appears in the daily digest when it is due.</p>
        </div>
      ) : (
        <div style={{ background: 'white', borderRadius: '8px', overflowX: 'auto', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #e0e0e0' }}>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Title</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Status</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Priority</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600', color: '#333' }}>Due Date</th>
                <th style={{ padding: '1rem' }}></th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t: any) => (
                <tr key={t.id} style={{ borderBottom: '1px solid #e0e0e0' }}>
                  <td style={{ padding: '1rem', color: '#333' }}>{t.title}</td>
                  <td style={{ padding: '1rem', color: '#666' }}>
                    <span style={{
                      background: t.status === 'done' ? '#d4edda' : t.status === 'in_progress' ? '#fff3cd' : '#e2e3e5',
                      color: t.status === 'done' ? '#155724' : t.status === 'in_progress' ? '#856404' : '#383d41',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '4px',
                      fontSize: '0.85rem'
                    }}>
                      {t.status}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', color: '#666' }}>{'⭐'.repeat(t.priority || 1)}</td>
                  <td style={{ padding: '1rem', color: '#666' }}>{t.due_date ? new Date(t.due_date).toLocaleDateString() : '-'}</td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    {t.status !== 'done' && (
                      <button
                        onClick={() => handleDone(t.id)}
                        style={{ padding: '0.5rem 1rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '500', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
                      >
                        <Check size={16} /> Done
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Task Modal */}
      {showAddModal && (
        <div
          onClick={() => !saving && setShowAddModal(false)}
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ background: 'white', borderRadius: '12px', padding: '2rem', maxWidth: '500px', width: '90%', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}
          >
            <h2 style={{ margin: '0 0 1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Plus size={24} style={{ color: '#667eea' }} /> Add task
            </h2>

            <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>Title</label>
                <input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  disabled={saving}
                  style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', fontFamily: 'inherit', boxSizing: 'border-box' }}
                />
                <p style={{ margin: '0.5rem 0 0', color: '#666', fontSize: '0.85rem' }}>
                  The title appears in your phone's daily digest, sent through ntfy.sh. Leave student names out.
                </p>
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>Due date</label>
                <input
                  type="date"
                  value={newDue}
                  onChange={(e) => setNewDue(e.target.value)}
                  disabled={saving}
                  style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', fontFamily: 'inherit', boxSizing: 'border-box' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={handleAddTask}
                disabled={!newTitle.trim() || saving}
                style={{ flex: 1, padding: '0.75rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '500', opacity: (!newTitle.trim() || saving) ? 0.6 : 1 }}
              >
                {saving ? 'Saving…' : 'Add task'}
              </button>
              <button
                onClick={() => setShowAddModal(false)}
                disabled={saving}
                style={{ flex: 1, padding: '0.75rem', background: '#f0f0f0', color: '#333', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '500', opacity: saving ? 0.6 : 1 }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Task Modal */}
      {showAIModal && (
        <div
          onClick={() => !generating && setShowAIModal(false)}
          style={{
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
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '2rem',
              maxWidth: '500px',
              width: '90%',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={24} style={{ color: '#667eea' }} /> AI Task Generator
              </h2>
              <button
                onClick={() => setShowAIModal(false)}
                disabled={generating}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#999'
                }}
              >
                ×
              </button>
            </div>

            <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>
                  Task Description
                </label>
                <textarea
                  value={aiPrompt}
                  onChange={(e) => setAIPrompt(e.target.value)}
                  placeholder="Describe what you want to accomplish. Qwen will refine it into a clear task..."
                  disabled={generating}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '1rem',
                    fontFamily: 'inherit',
                    resize: 'vertical',
                    minHeight: '100px',
                    opacity: generating ? 0.6 : 1
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>
                  Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value))}
                  disabled={generating}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '1rem',
                    opacity: generating ? 0.6 : 1
                  }}
                >
                  <option value={0}>Low (★)</option>
                  <option value={1}>Medium (★★)</option>
                  <option value={2}>High (★★★)</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={handleGenerateTask}
                disabled={!aiPrompt.trim() || generating}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '500',
                  opacity: (!aiPrompt.trim() || generating) ? 0.6 : 1
                }}
              >
                {generating ? '✨ Generating...' : '✨ Generate Task'}
              </button>
              <button
                onClick={() => setShowAIModal(false)}
                disabled={generating}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  background: '#f0f0f0',
                  color: '#333',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '500',
                  opacity: generating ? 0.6 : 1
                }}
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

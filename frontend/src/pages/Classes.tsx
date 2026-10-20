import React, { useState } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { List, Calendar } from 'lucide-react';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Classes() {
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
  const { data: classes = [], isLoading } = useQuery('classes', () =>
    axios.get(`/api/classes/`).then(r => r.data).catch(() => [])
  );

  if (isLoading) return <div className="loading">Loading classes...</div>;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>Classes & Courses</h1>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setViewMode('list')}
            style={{
              padding: '0.5rem 1rem',
              background: viewMode === 'list' ? '#667eea' : '#f0f0f0',
              color: viewMode === 'list' ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <List size={18} /> List
          </button>
          <button
            onClick={() => setViewMode('calendar')}
            style={{
              padding: '0.5rem 1rem',
              background: viewMode === 'calendar' ? '#667eea' : '#f0f0f0',
              color: viewMode === 'calendar' ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Calendar size={18} /> Calendar
          </button>
        </div>
      </div>

      {viewMode === 'list' && <ClassesList classes={classes} />}
      {viewMode === 'calendar' && <ClassesCalendar classes={classes} />}
    </div>
  );
}

function ClassesList({ classes }: { classes: any[] }) {
  const sorted = [...classes].sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      {sorted.map((cls) => (
        <div key={cls.id} style={{
          background: 'white',
          padding: '1.5rem',
          borderRadius: '8px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
            <h3 style={{ margin: 0, color: '#667eea' }}>{cls.name}</h3>
            <span style={{ background: '#e3f2fd', color: '#1976d2', padding: '0.3rem 0.8rem', borderRadius: '20px', fontSize: '0.85rem' }}>
              ${cls.price || 'Free'}
            </span>
          </div>
          <p style={{ color: '#666', margin: '0.5rem 0' }}>{cls.description}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginTop: '1rem', fontSize: '0.9rem' }}>
            <div>
              <strong>Instructor:</strong> {cls.instructor}
            </div>
            <div>
              <strong>Prerequisites:</strong> {cls.prerequisites || 'None'}
            </div>
            <div>
              <strong>Start:</strong> {new Date(cls.start_date).toLocaleDateString()} {new Date(cls.start_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div>
              <strong>End:</strong> {new Date(cls.end_date).toLocaleDateString()} {new Date(cls.end_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div>
              <strong>Duration:</strong> {Math.ceil((new Date(cls.end_date).getTime() - new Date(cls.start_date).getTime()) / (1000 * 60 * 60 * 24))} days
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ClassesCalendar({ classes }: { classes: any[] }) {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const classesInMonth = classes.filter(cls => {
    const classDate = new Date(cls.start_date);
    return classDate.getMonth() === currentMonth.getMonth() && classDate.getFullYear() === currentMonth.getFullYear();
  });

  const days = Array.from({ length: getDaysInMonth(currentMonth) }, (_, i) => i + 1);
  const firstDay = getFirstDayOfMonth(currentMonth);
  const emptyDays = Array.from({ length: firstDay }, () => null);

  const monthName = currentMonth.toLocaleString('default', { month: 'long', year: 'numeric' });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>{monthName}</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
            style={{ padding: '0.5rem 1rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            ← Prev
          </button>
          <button
            onClick={() => setCurrentMonth(new Date())}
            style={{ padding: '0.5rem 1rem', background: '#f0f0f0', color: '#333', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            Today
          </button>
          <button
            onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
            style={{ padding: '0.5rem 1rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            Next →
          </button>
        </div>
      </div>

      <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        {/* Weekday headers */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', background: '#667eea', color: 'white' }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} style={{ padding: '1rem', textAlign: 'center', fontWeight: 'bold' }}>
              {day}
            </div>
          ))}
        </div>

        {/* Calendar days */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', minHeight: '400px' }}>
          {emptyDays.map((_, i) => (
            <div key={`empty-${i}`} style={{ background: '#f9f9f9' }} />
          ))}
          {days.map((day) => {
            const dayDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
            const dayClasses = classesInMonth.filter(cls => new Date(cls.start_date).getDate() === day);

            return (
              <div
                key={day}
                style={{
                  padding: '0.75rem',
                  borderRight: '1px solid #e0e0e0',
                  borderBottom: '1px solid #e0e0e0',
                  minHeight: '120px',
                  background: dayClasses.length > 0 ? '#f0f4ff' : 'white'
                }}
              >
                <strong style={{ display: 'block', marginBottom: '0.5rem' }}>{day}</strong>
                {dayClasses.map((cls) => (
                  <div
                    key={cls.id}
                    style={{
                      fontSize: '0.75rem',
                      background: '#667eea',
                      color: 'white',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '3px',
                      marginBottom: '0.25rem',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                    title={cls.name}
                  >
                    {cls.name}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {classesInMonth.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Classes in {monthName}</h3>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {classesInMonth.map(cls => (
              <div key={cls.id} style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '6px', borderLeft: '4px solid #667eea' }}>
                <h4 style={{ margin: '0 0 0.5rem 0' }}>{cls.name}</h4>
                <p style={{ margin: '0.25rem 0', fontSize: '0.9rem', color: '#666' }}>
                  {new Date(cls.start_date).toLocaleDateString()} - {new Date(cls.end_date).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


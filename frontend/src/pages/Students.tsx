import React, { useState, useMemo } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { Search, Filter, X, Mail, Tag } from 'lucide-react';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Students() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedLists, setSelectedLists] = useState<string[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [sortBy, setSortBy] = useState('name');

  const { data: students = [], isLoading } = useQuery('students', () =>
    axios.get(`/api/students/`).then(r => r.data).catch(() => [])
  );

  // Extract unique tags and lists
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    students.forEach((s: any) => {
      if (s.tags) {
        s.tags.split(',').forEach((t: string) => tags.add(t.trim()));
      }
    });
    return Array.from(tags).sort();
  }, [students]);

  const allLists = useMemo(() => {
    const lists = new Set<string>();
    students.forEach((s: any) => {
      if (s.lists) {
        s.lists.split(',').forEach((l: string) => lists.add(l.trim()));
      }
    });
    return Array.from(lists).sort();
  }, [students]);

  // Filter and sort students
  const filteredStudents = useMemo(() => {
    let result = students.filter((student: any) => {
      const matchesSearch = searchTerm === '' ||
        student.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.email?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesTags = selectedTags.length === 0 || selectedTags.some(tag =>
        student.tags?.includes(tag)
      );

      const matchesLists = selectedLists.length === 0 || selectedLists.some(list =>
        student.lists?.includes(list)
      );

      return matchesSearch && matchesTags && matchesLists;
    });

    // Sort
    result.sort((a: any, b: any) => {
      switch(sortBy) {
        case 'name':
          return `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`);
        case 'email':
          return a.email.localeCompare(b.email);
        case 'recent':
          return new Date(b.enrollment_date).getTime() - new Date(a.enrollment_date).getTime();
        default:
          return 0;
      }
    });

    return result;
  }, [students, searchTerm, selectedTags, selectedLists, sortBy]);

  if (isLoading) return <div className="loading">Loading students...</div>;

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1>Student Directory</h1>
        <p style={{ color: '#666' }}>
          {filteredStudents.length} student{filteredStudents.length !== 1 ? 's' : ''} found • {students.length} total
        </p>
      </div>

      {/* Search and Filters */}
      <div style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '8px',
        marginBottom: '1.5rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem', marginBottom: '1rem' }}>
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '0.75rem', top: '0.75rem', color: '#999' }} />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 0.75rem 0.75rem 2.5rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '0.75rem',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#999'
                }}
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>

        {/* Lists Filter */}
        {allLists.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.9rem', color: '#666' }}>
              Filter by Lists:
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {allLists.map(list => (
                <button
                  key={list}
                  onClick={() => setSelectedLists(prev =>
                    prev.includes(list) ? prev.filter(l => l !== list) : [...prev, list]
                  )}
                  style={{
                    padding: '0.5rem 0.75rem',
                    background: selectedLists.includes(list) ? '#667eea' : '#f0f0f0',
                    color: selectedLists.includes(list) ? 'white' : '#333',
                    border: 'none',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    transition: 'all 0.2s'
                  }}
                >
                  {list}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.9rem', color: '#666' }}>
              Filter by Tags:
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTags(prev =>
                    prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
                  )}
                  style={{
                    padding: '0.5rem 0.75rem',
                    background: selectedTags.includes(tag) ? '#764ba2' : '#f0f0f0',
                    color: selectedTags.includes(tag) ? 'white' : '#333',
                    border: 'none',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    transition: 'all 0.2s'
                  }}
                >
                  <Tag size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Sort */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.9rem', color: '#666' }}>Sort:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '1px solid #ddd',
              borderRadius: '6px',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            <option value="name">Name</option>
            <option value="email">Email</option>
            <option value="recent">Recently Added</option>
          </select>
          {(selectedTags.length > 0 || selectedLists.length > 0) && (
            <button
              onClick={() => { setSelectedTags([]); setSelectedLists([]); }}
              style={{
                padding: '0.5rem 1rem',
                background: '#ff4757',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Students Grid */}
      {filteredStudents.length === 0 ? (
        <div style={{
          background: 'white',
          padding: '2rem',
          textAlign: 'center',
          borderRadius: '8px',
          color: '#999'
        }}>
          <p>No students found matching your search criteria</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {filteredStudents.map((student: any) => (
            <StudentCard
              key={student.id}
              student={student}
              onSelect={() => setSelectedStudent(student)}
            />
          ))}
        </div>
      )}

      {/* Student Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal
          student={selectedStudent}
          onClose={() => setSelectedStudent(null)}
        />
      )}
    </div>
  );
}

function StudentCard({ student, onSelect }: { student: any; onSelect: () => void }) {
  return (
    <div
      onClick={onSelect}
      style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '8px',
        border: '1px solid #e0e0e0',
        cursor: 'pointer',
        transition: 'all 0.2s',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        ':hover': { boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }
      }}
    >
      <h3 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>
        {student.first_name} {student.last_name}
      </h3>

      <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
        <p style={{ margin: 0, color: '#667eea' }}>📧 {student.email}</p>
        {student.phone && <p style={{ margin: 0, color: '#666' }}>📱 {student.phone}</p>}
        <p style={{ margin: 0, color: '#666' }}>📅 {new Date(student.enrollment_date).toLocaleDateString()}</p>
        <p style={{ margin: 0, color: '#666' }}>
          Status: <span style={{ background: student.status === 'active' ? '#d4edda' : '#f8d7da', color: student.status === 'active' ? '#155724' : '#721c24', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
            {student.status}
          </span>
        </p>
      </div>

      {student.lists && (
        <div style={{ marginBottom: '0.5rem' }}>
          <p style={{ margin: '0.25rem 0', fontSize: '0.8rem', color: '#666' }}>
            <strong>Lists:</strong> {student.lists}
          </p>
        </div>
      )}

      {student.tags && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
          {student.tags.split(',').map((tag: string, idx: number) => (
            <span
              key={idx}
              style={{
                background: '#764ba2',
                color: 'white',
                padding: '0.25rem 0.5rem',
                borderRadius: '12px',
                fontSize: '0.75rem'
              }}
            >
              {tag.trim()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function StudentDetailModal({ student, onClose }: { student: any; onClose: () => void }) {
  return (
    <div
      onClick={onClose}
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
          maxWidth: '600px',
          width: '90%',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>
            {student.first_name} {student.last_name}
          </h2>
          <button
            onClick={onClose}
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

        <div style={{ display: 'grid', gap: '1rem' }}>
          {/* Email */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Email</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <a href={`mailto:${student.email}`} style={{ color: '#667eea', textDecoration: 'none' }}>
                {student.email}
              </a>
              <Mail size={16} style={{ color: '#667eea', cursor: 'pointer' }} />
            </div>
          </div>

          {/* Phone */}
          {student.phone && (
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.25rem' }}>Phone</label>
              <p style={{ margin: 0, color: '#333' }}>{student.phone}</p>
            </div>
          )}

          {/* Lists */}
          {student.lists && (
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.5rem' }}>Lists</label>
              <p style={{ margin: 0, color: '#333' }}>{student.lists}</p>
            </div>
          )}

          {/* Tags */}
          {student.tags && (
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.5rem' }}>Tags</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {student.tags.split(',').map((tag: string, idx: number) => (
                  <span
                    key={idx}
                    style={{
                      background: '#764ba2',
                      color: 'white',
                      padding: '0.5rem 1rem',
                      borderRadius: '20px',
                      fontSize: '0.9rem'
                    }}
                  >
                    {tag.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Status */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.25rem' }}>Status</label>
            <span style={{
              background: student.status === 'active' ? '#d4edda' : '#f8d7da',
              color: student.status === 'active' ? '#155724' : '#721c24',
              padding: '0.5rem 1rem',
              borderRadius: '20px',
              fontSize: '0.9rem',
              display: 'inline-block'
            }}>
              {student.status}
            </span>
          </div>

          {/* Enrollment Date */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.25rem' }}>Enrollment Date</label>
            <p style={{ margin: 0, color: '#333' }}>
              {new Date(student.enrollment_date).toLocaleDateString()} {new Date(student.enrollment_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>

          {/* Created At */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.25rem' }}>Created</label>
            <p style={{ margin: 0, color: '#999', fontSize: '0.85rem' }}>
              {new Date(student.created_at).toLocaleDateString()} {new Date(student.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>

          {/* Updated At */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', color: '#666', marginBottom: '0.25rem' }}>Last Updated</label>
            <p style={{ margin: 0, color: '#999', fontSize: '0.85rem' }}>
              {new Date(student.updated_at).toLocaleDateString()} {new Date(student.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            marginTop: '1.5rem',
            width: '100%',
            padding: '0.75rem',
            background: '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
}

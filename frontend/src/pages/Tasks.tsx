import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Tasks() {
  const { data: tasks = [] } = useQuery('tasks', () =>
    axios.get(`${API_URL}/tasks`).then(r => r.data).catch(() => [])
  );

  return (
    <div className="page">
      <h1>Tasks</h1>
      <button className="btn-primary">➕ New Task</button>
      <table className="data-table">
        <thead>
          <tr><th>Title</th><th>Status</th><th>Priority</th><th>Due Date</th></tr>
        </thead>
        <tbody>
          {tasks.map((t: any) => <tr key={t.id}><td>{t.title}</td><td>{t.status}</td><td>{t.priority}</td><td>{t.due_date ? new Date(t.due_date).toLocaleDateString() : '-'}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}

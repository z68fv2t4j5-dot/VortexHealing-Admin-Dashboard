import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Classes() {
  const { data: classes = [] } = useQuery('classes', () =>
    axios.get(`${API_URL}/classes`).then(r => r.data).catch(() => [])
  );

  return (
    <div className="page">
      <h1>Classes</h1>
      <button className="btn-primary">➕ Add Class</button>
      <table className="data-table">
        <thead>
          <tr><th>Name</th><th>Instructor</th><th>Capacity</th><th>Schedule</th></tr>
        </thead>
        <tbody>
          {classes.map((c: any) => <tr key={c.id}><td>{c.name}</td><td>{c.instructor}</td><td>{c.capacity}</td><td>{c.schedule}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}

import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Students() {
  const { data: students = [], isLoading } = useQuery('students', () =>
    axios.get(`${API_URL}/students`).then(r => r.data).catch(() => [])
  );

  if (isLoading) return <div className="loading">Loading...</div>;

  return (
    <div className="page">
      <h1>Students Management</h1>
      <button className="btn-primary">➕ Add Student</button>
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Enrollment Date</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {students.map((student: any) => (
            <tr key={student.id}>
              <td>{student.first_name} {student.last_name}</td>
              <td>{student.email}</td>
              <td>{student.phone}</td>
              <td>{new Date(student.enrollment_date).toLocaleDateString()}</td>
              <td><span className="badge">{student.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

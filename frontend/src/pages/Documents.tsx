import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Documents() {
  const { data: docs = [] } = useQuery('documents', () =>
    axios.get(`${API_URL}/documents`).then(r => r.data).catch(() => [])
  );

  return (
    <div className="page">
      <h1>Accounting Documents</h1>
      <button className="btn-primary">📤 Upload Document</button>
      <table className="data-table">
        <thead>
          <tr><th>Filename</th><th>Type</th><th>Uploaded</th><th>Action</th></tr>
        </thead>
        <tbody>
          {docs.map((d: any) => (
            <tr key={d.id}>
              <td>{d.filename}</td>
              <td>{d.doc_type}</td>
              <td>{new Date(d.created_at).toLocaleDateString()}</td>
              <td><button className="btn-small">View</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

export default function Email() {
  const { data: campaigns = [] } = useQuery('emails', () =>
    axios.get(`${API_URL}/emails`).then(r => r.data).catch(() => [])
  );

  return (
    <div className="page">
      <h1>Email Campaigns</h1>
      <button className="btn-primary">➕ New Campaign</button>
      <table className="data-table">
        <thead>
          <tr><th>Name</th><th>Subject</th><th>Recipients</th><th>Status</th></tr>
        </thead>
        <tbody>
          {campaigns.map((c: any) => <tr key={c.id}><td>{c.name}</td><td>{c.subject}</td><td>{c.recipients}</td><td>{c.sent ? 'Sent' : 'Pending'}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}

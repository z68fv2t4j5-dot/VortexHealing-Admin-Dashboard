import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = '/api';

export default function Events() {
  const { data: events = [] } = useQuery('events', () =>
    axios.get(`${API_URL}/events`).then(r => r.data).catch(() => [])
  );

  return (
    <div className="page">
      <h1>Events</h1>
      <button className="btn-primary">➕ New Event</button>
      <table className="data-table">
        <thead>
          <tr><th>Title</th><th>Type</th><th>Date</th><th>Location</th></tr>
        </thead>
        <tbody>
          {events.map((e: any) => <tr key={e.id}><td>{e.title}</td><td>{e.event_type}</td><td>{new Date(e.start_time).toLocaleDateString()}</td><td>{e.location}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}

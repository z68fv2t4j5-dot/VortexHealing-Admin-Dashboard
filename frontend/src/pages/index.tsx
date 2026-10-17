import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = 'http://localhost:8000/api';

const Classes = () => {
  const { data: classes = [] } = useQuery('classes', () =>
    axios.get(`${API_URL}/classes`).then(r => r.data).catch(() => [])
  );
  return <PageTemplate title="Classes" data={classes} columns={['name', 'instructor', 'capacity', 'schedule']} />;
};

const Events = () => {
  const { data: events = [] } = useQuery('events', () =>
    axios.get(`${API_URL}/events`).then(r => r.data).catch(() => [])
  );
  return <PageTemplate title="Events" data={events} columns={['title', 'event_type', 'start_time', 'location']} />;
};

const Tasks = () => {
  const { data: tasks = [] } = useQuery('tasks', () =>
    axios.get(`${API_URL}/tasks`).then(r => r.data).catch(() => [])
  );
  return <PageTemplate title="Tasks" data={tasks} columns={['title', 'status', 'priority', 'due_date']} />;
};

const Email = () => {
  const { data: campaigns = [] } = useQuery('campaigns', () =>
    axios.get(`${API_URL}/emails`).then(r => r.data).catch(() => [])
  );
  return <PageTemplate title="Email Campaigns" data={campaigns} columns={['name', 'subject', 'sent', 'scheduled_time']} />;
};

const Ideas = () => {
  const { data: ideas = [] } = useQuery('ideas', () =>
    axios.get(`${API_URL}/ideas`).then(r => r.data).catch(() => [])
  );
  return <PageTemplate title="Growth Ideas" data={ideas} columns={['title', 'category', 'potential_impact', 'status']} />;
};

const Documents = () => {
  const { data: docs = [] } = useQuery('documents', () =>
    axios.get(`${API_URL}/documents`).then(r => r.data).catch(() => [])
  );
  return <PageTemplate title="Documents" data={docs} columns={['filename', 'doc_type', 'created_at']} />;
};

function PageTemplate({ title, data, columns }: any) {
  return (
    <div className="page">
      <h1>{title}</h1>
      <button className="btn-primary">➕ Add New</button>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col: string) => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.map((row: any, idx: number) => (
            <tr key={idx}>
              {columns.map((col: string) => <td key={col}>{String(row[col]).substring(0, 50)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { Classes, Events, Tasks, Email, Ideas, Documents };

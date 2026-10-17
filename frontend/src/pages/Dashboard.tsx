import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { TrendingUp, AlertCircle, Users, BookOpen, Calendar, CheckSquare } from 'lucide-react';
import '../styles/Dashboard.css';

const API_URL = 'http://localhost:8000/api';

export default function Dashboard() {
  const { data: tasks = [] } = useQuery('tasks', () =>
    axios.get(`${API_URL}/tasks`).then(r => r.data).catch(() => [])
  );

  const { data: students = [] } = useQuery('students', () =>
    axios.get(`${API_URL}/students`).then(r => r.data).catch(() => [])
  );

  const stats = [
    { icon: <Users size={24} />, label: 'Students', value: students.length, color: 'blue' },
    { icon: <CheckSquare size={24} />, label: 'Tasks', value: tasks.length, color: 'green' },
    { icon: <AlertCircle size={24} />, label: 'Pending', value: tasks.filter((t: any) => t.status === 'todo').length, color: 'orange' },
    { icon: <TrendingUp size={24} />, label: 'Growth', value: '5 Ideas', color: 'purple' },
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard Overview</h1>
        <p>Welcome to VortexHealing Admin Dashboard</p>
      </div>

      <div className="stats-grid">
        {stats.map((stat, idx) => (
          <div key={idx} className={`stat-card stat-${stat.color}`}>
            {stat.icon}
            <h3>{stat.label}</h3>
            <p>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="dashboard-sections">
        <div className="recent-tasks">
          <h2>Recent Tasks</h2>
          {tasks.slice(0, 5).map((task: any) => (
            <div key={task.id} className="task-item">
              <h4>{task.title}</h4>
              <span className={`status status-${task.status}`}>{task.status}</span>
            </div>
          ))}
        </div>

        <div className="quick-actions">
          <h2>Quick Actions</h2>
          <button className="action-btn">➕ New Student</button>
          <button className="action-btn">📅 New Event</button>
          <button className="action-btn">✉️ Send Email Campaign</button>
          <button className="action-btn">💡 Generate Ideas</button>
        </div>
      </div>
    </div>
  );
}

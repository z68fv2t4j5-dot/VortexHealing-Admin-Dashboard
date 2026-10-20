import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard, Users, Globe, BookOpen, Calendar, CheckSquare, MessageCircle, Mail, Lightbulb, FileText, Library } from 'lucide-react';
import '../styles/Navigation.css';

export default function Navigation() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>VortexHealing</h1>
        <p>Admin Dashboard</p>
      </div>
      <ul className="nav-links">
        <li><Link to="/"><LayoutDashboard size={20} /> Dashboard</Link></li>
        <li><Link to="/students"><Users size={20} /> Students</Link></li>
        <li><Link to="/global-students"><Globe size={20} /> Global Students</Link></li>
        <li><Link to="/classes"><BookOpen size={20} /> Classes</Link></li>
        <li><Link to="/events"><Calendar size={20} /> Events</Link></li>
        <li><Link to="/tasks"><CheckSquare size={20} /> Tasks</Link></li>
        <li><Link to="/handouts"><Library size={20} /> Handouts</Link></li>
        <li><Link to="/chat"><MessageCircle size={20} /> Chat</Link></li>
        <li><Link to="/email"><Mail size={20} /> Email</Link></li>
        <li><Link to="/ideas"><Lightbulb size={20} /> Growth Ideas</Link></li>
        <li><Link to="/documents"><FileText size={20} /> Documents</Link></li>
      </ul>
    </nav>
  );
}

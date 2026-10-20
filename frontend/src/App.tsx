import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import Students from './pages/Students';
import GlobalStudents from './pages/GlobalStudents';
import Classes from './pages/Classes';
import Events from './pages/Events';
import Tasks from './pages/Tasks';
import Email from './pages/Email';
import Ideas from './pages/Ideas';
import Documents from './pages/Documents';
import Chat from './pages/Chat';
import Handouts from './pages/Handouts';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app">
          <Navigation />
          <main className="app-main">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/students" element={<Students />} />
              <Route path="/global-students" element={<GlobalStudents />} />
              <Route path="/classes" element={<Classes />} />
              <Route path="/events" element={<Events />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/handouts" element={<Handouts />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/email" element={<Email />} />
              <Route path="/ideas" element={<Ideas />} />
              <Route path="/documents" element={<Documents />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

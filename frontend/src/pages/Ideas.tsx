import React from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import '../styles/Pages.css';

const API_URL = '/api';

export default function Ideas() {
  const queryClient = useQueryClient();
  const { data: ideas = [] } = useQuery('ideas', () =>
    axios.get(`${API_URL}/ideas`).then(r => r.data).catch(() => [])
  );

  const generateMutation = useMutation(
    (category: string) => axios.post(`${API_URL}/ideas/generate?category=${category}`),
    { onSuccess: () => queryClient.invalidateQueries('ideas') }
  );

  return (
    <div className="page">
      <h1>Growth Ideas</h1>
      <div className="actions">
        <button className="btn-primary" onClick={() => generateMutation.mutate('student_growth')}>
          ✨ Generate Ideas with AI
        </button>
      </div>
      <div className="ideas-list">
        {ideas.map((idea: any) => (
          <div key={idea.id} className="idea-card">
            <h3>{idea.title}</h3>
            <p>{idea.description.substring(0, 200)}...</p>
            <div className="idea-meta">
              <span className="badge">{idea.category}</span>
              <span className="badge">{idea.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

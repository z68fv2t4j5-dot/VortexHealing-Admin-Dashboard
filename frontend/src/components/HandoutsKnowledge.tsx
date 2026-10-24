import { useState } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { ExternalLink } from 'lucide-react';

export interface Source {
  section_id: number;
  document_id: number;
  title: string;
  heading_path: string;
  class: string | null;
}

interface Fact {
  predicate: string;
  object: string;
  object_id: number | null;
  detail: string;
  level: string | null;
  source: Source;
}

interface IncomingFact {
  predicate: string;
  subject: string;
  subject_id: number;
  detail: string;
  source: Source;
}

export interface EntityCardData {
  id: number;
  name: string;
  type: string | null;
  aliases: string[];
  introduced_in: string[];
  definitions: { text: string; source: Source }[];
  facts: Fact[];
  incoming: IncomingFact[];
}

const box = { background: 'white', padding: '1.25rem 1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' };

const HEADINGS: Record<string, string> = {
  done_in_class: 'How it is done, by class',
  releases: 'Releases or clears',
  is_source_of: 'Is a source of',
  requires: 'Requires',
  located_in: 'Where it sits',
  is_part_of: 'Part of',
  related_to: 'Related',
};

const INCOMING: Record<string, string> = {
  releases: 'Released or cleared by',
  is_source_of: 'Comes from',
  is_part_of: 'Has parts',
  requires: 'Needed by',
  introduced_in: 'Introduced in this class',
  done_in_class: 'Done in this class',
  located_in: 'Contains',
  related_to: 'Related',
};

function SourceLink({ source }: { source: Source }) {
  return (
    <a href={`/api/handouts/file/${source.document_id}`} target="_blank" rel="noreferrer"
      title={source.heading_path || 'opening section'}
      style={{ color: '#999', fontSize: '0.8rem', textDecoration: 'none', whiteSpace: 'nowrap' }}>
      {source.title} <ExternalLink size={11} />
    </a>
  );
}

function EntityLink({ id, name, onOpen }: { id: number | null; name: string; onOpen: (id: number) => void }) {
  return id
    ? <button onClick={() => onOpen(id)} style={{ background: 'none', border: 'none', padding: 0, color: '#667eea', cursor: 'pointer', font: 'inherit' }}>{name}</button>
    : <span>{name}</span>;
}

// One entry of the knowledge map: what it is, where it is introduced, and every fact with its handout.
export function EntityCard({ data, onOpen }: { data: EntityCardData; onOpen: (id: number) => void }) {
  const [showAll, setShowAll] = useState(false);
  const groups: Record<string, Fact[]> = {};
  data.facts.filter(f => f.predicate !== 'introduced_in').forEach(f => { (groups[f.predicate] ||= []).push(f); });
  const incoming: Record<string, IncomingFact[]> = {};
  data.incoming.forEach(f => { (incoming[f.predicate] ||= []).push(f); });
  const limit = showAll ? 99 : 4;

  return (
    <div style={{ ...box, borderTop: '4px solid #667eea' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', flexWrap: 'wrap' }}>
        <h3 style={{ margin: 0 }}>{data.name}</h3>
        {data.type && <span style={{ fontSize: '0.75rem', background: '#eef0ff', color: '#667eea', padding: '0.1rem 0.5rem', borderRadius: '10px' }}>{data.type}</span>}
        {data.aliases.length > 0 && <span style={{ fontSize: '0.8rem', color: '#999' }}>also: {data.aliases.join(', ')}</span>}
      </div>
      {data.introduced_in.length > 0 && (
        <p style={{ margin: '0.5rem 0 0', color: '#333' }}>
          <strong>Introduced in:</strong> {data.introduced_in.join(', ')}
        </p>
      )}
      {data.definitions[0] && (
        <p style={{ margin: '0.5rem 0 0', color: '#555', lineHeight: 1.5 }}>
          {data.definitions[0].text} <SourceLink source={data.definitions[0].source} />
        </p>
      )}
      {Object.entries(groups).map(([predicate, facts]) => (
        <div key={predicate} style={{ marginTop: '0.75rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#666', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            {HEADINGS[predicate] || predicate}
          </div>
          {facts.slice(0, limit).map((f, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'baseline', margin: '0.2rem 0' }}>
              <EntityLink id={f.object_id} name={f.object} onOpen={onOpen} />
              {f.detail && <span style={{ color: '#555' }}>— {f.detail}</span>}
              <SourceLink source={f.source} />
            </div>
          ))}
        </div>
      ))}
      {Object.entries(incoming).map(([predicate, facts]) => (
        <div key={`in-${predicate}`} style={{ marginTop: '0.75rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#666', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            {INCOMING[predicate] || predicate}
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.2rem' }}>
            {facts.slice(0, showAll ? 99 : 8).map((f, i) => <EntityLink key={i} id={f.subject_id} name={f.subject} onOpen={onOpen} />)}
          </div>
        </div>
      ))}
      {(data.facts.length > 8 || data.incoming.length > 8) && (
        <button onClick={() => setShowAll(!showAll)}
          style={{ marginTop: '0.75rem', background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', padding: 0 }}>
          {showAll ? 'Show less' : 'Show everything'}
        </button>
      )}
    </div>
  );
}

// Loads a card by id, so links inside cards and the Browse list can open any entry.
export function EntityCardById({ id, onOpen }: { id: number; onOpen: (id: number) => void }) {
  const { data, isLoading } = useQuery(['handouts-entity', id], () => axios.get(`/api/handouts/entity/${id}`).then(r => r.data));
  if (isLoading || !data) return <div style={{ ...box, color: '#999' }}>Loading…</div>;
  return <EntityCard data={data} onOpen={onOpen} />;
}

const TYPES = [
  ['', 'Everything'], ['tool', 'Tools'], ['transmission', 'Transmissions'], ['class', 'Classes'],
  ['conditioning', 'Conditioning'], ['structure', 'Structures'], ['protocol', 'Protocols'],
  ['being', 'Beings'], ['place', 'Places'], ['concept', 'Concepts'],
];

// Every entry in the knowledge map, filterable by kind and name; selecting one shows its card.
export function KnowledgeBrowse() {
  const [kind, setKind] = useState('');
  const [filter, setFilter] = useState('');
  const [open, setOpen] = useState<number | null>(null);
  const { data } = useQuery(['handouts-entities', kind, filter], () =>
    axios.get('/api/handouts/entities', { params: { type: kind || undefined, q: filter } }).then(r => r.data), { keepPreviousData: true });
  const counts: Record<string, number> = data?.types || {};

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <div style={{ ...box, display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        {TYPES.map(([id, label]) => (
          <button key={id} onClick={() => { setKind(id); setOpen(null); }}
            style={{ padding: '0.35rem 0.8rem', borderRadius: '14px', border: 'none', cursor: 'pointer',
              background: kind === id ? '#667eea' : '#f0f0f0', color: kind === id ? 'white' : '#333', fontSize: '0.85rem' }}>
            {label}{id && counts[id] ? ` (${counts[id]})` : ''}
          </button>
        ))}
        <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter by name…"
          style={{ marginLeft: 'auto', padding: '0.4rem 0.75rem', border: '1px solid #ddd', borderRadius: '6px', minWidth: '12rem' }} />
      </div>
      {open !== null && <EntityCardById id={open} onOpen={setOpen} />}
      <div style={{ ...box, display: 'flex', flexWrap: 'wrap', gap: '0.4rem 1rem' }}>
        {(data?.entities || []).map((e: { id: number; name: string; n: number }) => (
          <button key={e.id} onClick={() => setOpen(e.id)}
            style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: open === e.id ? '#333' : '#667eea', font: 'inherit' }}>
            {e.name} <span style={{ color: '#bbb', fontSize: '0.8rem' }}>{e.n}</span>
          </button>
        ))}
        {data && data.entities.length === 0 && <span style={{ color: '#999' }}>Nothing in the knowledge map yet.</span>}
      </div>
    </div>
  );
}

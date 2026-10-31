// Answer text as Qwen writes it: a little Markdown and [n] citations.

// Inline answer text: **bold**, and [3] as a link that scrolls to passage 3.
function inline(text: string, key: string, linkCitations: boolean) {
  return text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, i) => {
    const cite = part.match(/^\[(\d+)\]$/);
    if (cite && linkCitations) {
      return <a key={`${key}-${i}`} href={`#passage-${cite[1]}`} style={{ color: '#667eea', fontWeight: 600, textDecoration: 'none' }}>{part}</a>;
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={`${key}-${i}`}>{part.slice(2, -2)}</strong>;
    return part;
  });
}

// The small amount of Markdown Qwen writes: headings, bullet and numbered lines, paragraphs.
export function renderAnswer(answer: string, linkCitations = true) {
  return answer.split('\n').map((line, i) => {
    const key = String(i);
    const heading = line.match(/^#{1,6}\s+(.*)/);
    if (heading) return <h4 key={key} style={{ margin: '1rem 0 0.25rem', color: '#333' }}>{inline(heading[1], key, linkCitations)}</h4>;
    const bullet = line.match(/^\s*([-*•]|\d+[.)])\s+(.*)/);
    if (bullet) {
      return (
        <div key={key} style={{ display: 'flex', gap: '0.5rem', margin: '0.2rem 0 0.2rem 0.5rem' }}>
          <span style={{ color: '#667eea' }}>{/\d/.test(bullet[1]) ? bullet[1] : '•'}</span>
          <span>{inline(bullet[2], key, linkCitations)}</span>
        </div>
      );
    }
    if (!line.trim()) return <div key={key} style={{ height: '0.5rem' }} />;
    return <p key={key} style={{ margin: '0.25rem 0' }}>{inline(line, key, linkCitations)}</p>;
  });
}

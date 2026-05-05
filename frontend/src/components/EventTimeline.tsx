import { useEffect, useRef } from 'react';
import type { AgentEvent } from '../types';
import { formatDate } from '../utils/format';

interface EventTimelineProps {
  events: AgentEvent[];
}

export function EventTimeline({ events }: EventTimelineProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [events.length]);

  return (
    <section className="panel event-panel">
      <div className="panel-header">
        <h2>Event Timeline</h2>
        <span className="muted">{events.length} events</span>
      </div>
      <div className="event-list">
        {events.map((event, index) => (
          <article className="event-item" key={`${event.created_at}-${event.from_agent}-${event.type}-${index}`}>
            <div className="event-head">
              <span className="event-type">{event.type}</span>
              <span className="muted">{formatDate(event.created_at)}</span>
            </div>
            <div className="event-route">
              <strong>{event.from_agent}</strong>
              {event.to_agent && <span>to {event.to_agent}</span>}
            </div>
            <p>{event.content}</p>
            {event.artifact_refs.length > 0 && <span className="artifact-ref">{event.artifact_refs.join(', ')}</span>}
          </article>
        ))}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}

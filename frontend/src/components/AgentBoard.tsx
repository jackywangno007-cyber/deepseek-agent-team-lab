import type { AgentEvent } from '../types';
import { deriveAgentStatuses } from '../utils/agentStatus';
import { formatDate } from '../utils/format';
import { StatusBadge } from './StatusBadge';

interface AgentBoardProps {
  events: AgentEvent[];
  hasSelectedTask: boolean;
}

export function AgentBoard({ events, hasSelectedTask }: AgentBoardProps) {
  const agents = deriveAgentStatuses(events, hasSelectedTask);
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Agent Board</h2>
      </div>
      <div className="agent-grid">
        {agents.map((agent) => (
          <article className="agent-card" key={agent.name}>
            <div className="agent-card-top">
              <strong>{agent.name}</strong>
              <StatusBadge status={agent.status} />
            </div>
            <p>{agent.role}</p>
            <dl>
              <div>
                <dt>Output</dt>
                <dd>{agent.outputArtifact || '-'}</dd>
              </div>
              <div>
                <dt>Last event</dt>
                <dd>{formatDate(agent.lastEventTime)}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

import type { AgentEvent } from '../types';

export type DerivedAgentStatus = 'IDLE' | 'WAITING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface AgentDefinition {
  name: string;
  role: string;
  outputArtifact?: string;
}

export interface AgentStatusInfo extends AgentDefinition {
  status: DerivedAgentStatus;
  lastEventTime?: string;
}

export const AGENTS: AgentDefinition[] = [
  { name: 'ManagerAgent', role: 'Coordinator', outputArtifact: 'final_summary.md' },
  { name: 'ProductAgent', role: 'Product requirements', outputArtifact: 'prd.md' },
  { name: 'ArchitectAgent', role: 'System architecture', outputArtifact: 'architecture.md' },
  { name: 'FrontendAgent', role: 'Frontend planning', outputArtifact: 'frontend_plan.md' },
  { name: 'BackendAgent', role: 'Backend API design', outputArtifact: 'api_design.md' },
  { name: 'TestAgent', role: 'Test strategy', outputArtifact: 'test_plan.md' },
  { name: 'ReviewerAgent', role: 'Quality review', outputArtifact: 'review_report.md' },
];

export function deriveAgentStatuses(events: AgentEvent[], hasSelectedTask: boolean): AgentStatusInfo[] {
  return AGENTS.map((agent) => {
    const agentEvents = events.filter((event) => event.from_agent === agent.name || event.to_agent === agent.name);
    const ownEvents = events.filter((event) => event.from_agent === agent.name);
    const lastEvent = agentEvents[agentEvents.length - 1];
    const hasFailure = ownEvents.some((event) => event.type === 'error' || event.status === 'failed');
    const hasCompleted = ownEvents.some((event) => {
      if (agent.name === 'ManagerAgent') {
        return event.type === 'final_summary' || event.type === 'agent_completed';
      }
      return event.type === 'agent_completed';
    });
    const hasStarted = ownEvents.some((event) => event.type === 'agent_started');
    const hasAssignment = agentEvents.some((event) => event.type === 'task_assign' || event.type === 'review_request');

    let status: DerivedAgentStatus = hasSelectedTask ? 'WAITING' : 'IDLE';
    if (hasFailure) {
      status = 'FAILED';
    } else if (hasCompleted) {
      status = 'COMPLETED';
    } else if (hasStarted) {
      status = 'RUNNING';
    } else if (hasAssignment) {
      status = 'WAITING';
    }

    return {
      ...agent,
      status,
      lastEventTime: lastEvent?.created_at,
    };
  });
}

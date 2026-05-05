export type TaskStatus = 'CREATED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | string;

export interface HealthResponse {
  status: string;
  version: string;
}

export interface TaskMeta {
  task_id: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  workspace_path?: string;
  mock: boolean;
  model: string;
  task_input_preview: string;
  error?: string | null;
}

export interface TaskCreateRequest {
  task: string;
  mock: boolean;
  model?: string;
  run_async: boolean;
}

export interface TaskCreateResponse {
  task_id: string;
  status: TaskStatus;
  workspace_path: string;
}

export interface AgentEvent {
  task_id?: string;
  from_agent: string;
  to_agent?: string | null;
  type: string;
  content: string;
  artifact_refs: string[];
  status: string;
  created_at: string;
}

export interface ArtifactInfo {
  name: string;
  path: string;
  size_bytes: number;
  modified_at: string;
}

export interface ArtifactContent {
  task_id: string;
  artifact_name: string;
  content: string;
}

export interface EvaluationResult {
  artifacts_complete?: boolean;
  events_complete?: boolean;
  review_score_found?: boolean;
  final_summary_found?: boolean;
  passed?: boolean;
  [key: string]: boolean | string | number | undefined;
}

export interface WebSocketEventMessage {
  type: 'event';
  data: AgentEvent;
}

export interface WebSocketFinishedMessage {
  type: 'task_finished';
  status: TaskStatus;
}

export interface WebSocketErrorMessage {
  type: 'error';
  message: string;
}

export type TaskWebSocketMessage = WebSocketEventMessage | WebSocketFinishedMessage | WebSocketErrorMessage;

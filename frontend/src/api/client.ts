import type {
  AgentEvent,
  ArtifactContent,
  ArtifactInfo,
  ArtifactVersionInfo,
  CreateFeedbackRequest,
  CreateFeedbackResponse,
  EvaluationResult,
  HealthResponse,
  HumanFeedback,
  RevisionRecord,
  RevisionRequest,
  RevisionResponse,
  TaskCreateRequest,
  TaskCreateResponse,
  TaskMeta,
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (options?.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the generic message.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/api/health');
}

export function createTask(payload: TaskCreateRequest): Promise<TaskCreateResponse> {
  return requestJson<TaskCreateResponse>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listTasks(): Promise<TaskMeta[]> {
  const payload = await requestJson<{ tasks: TaskMeta[] }>('/api/tasks');
  return payload.tasks;
}

export function getTask(taskId: string): Promise<TaskMeta> {
  return requestJson<TaskMeta>(`/api/tasks/${encodeURIComponent(taskId)}`);
}

export async function getTaskEvents(taskId: string): Promise<AgentEvent[]> {
  const payload = await requestJson<{ events: AgentEvent[] }>(`/api/tasks/${encodeURIComponent(taskId)}/events`);
  return payload.events;
}

export async function listArtifacts(taskId: string): Promise<ArtifactInfo[]> {
  const payload = await requestJson<{ artifacts: ArtifactInfo[] }>(`/api/tasks/${encodeURIComponent(taskId)}/artifacts`);
  return payload.artifacts;
}

export async function getArtifact(taskId: string, artifactName: string): Promise<ArtifactContent> {
  const encodedName = artifactName.split('/').map(encodeURIComponent).join('/');
  return requestJson<ArtifactContent>(`/api/tasks/${encodeURIComponent(taskId)}/artifacts/${encodedName}`);
}

export async function getEvaluation(taskId: string): Promise<EvaluationResult> {
  const payload = await requestJson<{ evaluation: EvaluationResult }>(`/api/tasks/${encodeURIComponent(taskId)}/evaluation`);
  return payload.evaluation;
}

export function buildTaskEventsWebSocketUrl(taskId: string): string {
  const wsBase = API_BASE_URL.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
  return `${wsBase}/ws/tasks/${encodeURIComponent(taskId)}/events`;
}

export function createFeedback(taskId: string, payload: CreateFeedbackRequest): Promise<CreateFeedbackResponse> {
  return requestJson<CreateFeedbackResponse>(`/api/tasks/${encodeURIComponent(taskId)}/feedback`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listFeedback(taskId: string): Promise<HumanFeedback[]> {
  const payload = await requestJson<{ feedback: HumanFeedback[] }>(`/api/tasks/${encodeURIComponent(taskId)}/feedback`);
  return payload.feedback;
}

export function requestRevision(taskId: string, payload: RevisionRequest): Promise<RevisionResponse> {
  return requestJson<RevisionResponse>(`/api/tasks/${encodeURIComponent(taskId)}/revisions`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listRevisions(taskId: string): Promise<RevisionRecord[]> {
  const payload = await requestJson<{ revisions: RevisionRecord[] }>(`/api/tasks/${encodeURIComponent(taskId)}/revisions`);
  return payload.revisions;
}

export async function listArtifactVersions(taskId: string, artifactName: string): Promise<ArtifactVersionInfo[]> {
  const encodedName = encodeURIComponent(artifactName);
  const payload = await requestJson<{ versions: ArtifactVersionInfo[] }>(
    `/api/tasks/${encodeURIComponent(taskId)}/artifacts/${encodedName}/versions`,
  );
  return payload.versions;
}

export async function getArtifactVersion(taskId: string, artifactName: string, versionName: string): Promise<ArtifactContent> {
  return requestJson<ArtifactContent>(
    `/api/tasks/${encodeURIComponent(taskId)}/artifacts/${encodeURIComponent(artifactName)}/versions/${encodeURIComponent(versionName)}`,
  );
}

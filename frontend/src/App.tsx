import { useCallback, useEffect, useRef, useState } from 'react';
import {
  buildTaskEventsWebSocketUrl,
  createTask,
  getArtifact,
  getEvaluation,
  getHealth,
  getTask,
  getTaskEvents,
  listArtifacts,
  listTasks,
} from './api/client';
import { AgentBoard } from './components/AgentBoard';
import { ArtifactExplorer } from './components/ArtifactExplorer';
import { ArtifactViewer } from './components/ArtifactViewer';
import { EvaluationPanel } from './components/EvaluationPanel';
import { EventTimeline } from './components/EventTimeline';
import { Layout } from './components/Layout';
import { TaskCreator } from './components/TaskCreator';
import { TaskList } from './components/TaskList';
import type { AgentEvent, ArtifactInfo, EvaluationResult, TaskMeta, TaskWebSocketMessage } from './types';

function eventKey(event: AgentEvent): string {
  return [event.created_at, event.from_agent, event.to_agent || '', event.type, event.content].join('|');
}

function uniqueEvents(events: AgentEvent[]): AgentEvent[] {
  const seen = new Set<string>();
  const result: AgentEvent[] = [];
  for (const event of events) {
    const key = eventKey(event);
    if (!seen.has(key)) {
      seen.add(key);
      result.push(event);
    }
  }
  return result;
}

function friendlyError(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

export default function App() {
  const [backendStatus, setBackendStatus] = useState('CHECKING');
  const [tasks, setTasks] = useState<TaskMeta[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskMeta | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactInfo[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | undefined>();
  const [artifactContent, setArtifactContent] = useState<string | undefined>();
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [taskLoading, setTaskLoading] = useState(false);
  const [taskListLoading, setTaskListLoading] = useState(false);
  const [artifactLoading, setArtifactLoading] = useState(false);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [taskListError, setTaskListError] = useState<string | null>(null);
  const [artifactError, setArtifactError] = useState<string | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [websocketStatus, setWebsocketStatus] = useState('IDLE');
  const socketRef = useRef<WebSocket | null>(null);

  const refreshTasks = useCallback(async () => {
    setTaskListLoading(true);
    setTaskListError(null);
    try {
      setTasks(await listTasks());
    } catch (error) {
      setTaskListError(friendlyError(error, 'Could not load tasks. Is the backend running?'));
    } finally {
      setTaskListLoading(false);
    }
  }, []);

  const refreshSelectedTask = useCallback(async (taskId: string) => {
    const meta = await getTask(taskId);
    setSelectedTask(meta);
    return meta;
  }, []);

  const loadEvents = useCallback(async (taskId: string) => {
    setEvents(uniqueEvents(await getTaskEvents(taskId)));
  }, []);

  const loadArtifacts = useCallback(async (taskId: string) => {
    setArtifactLoading(true);
    setArtifactError(null);
    try {
      const nextArtifacts = await listArtifacts(taskId);
      setArtifacts(nextArtifacts);
      setSelectedArtifact((current) => {
        if (nextArtifacts.length === 0) {
          return undefined;
        }
        if (current && nextArtifacts.some((artifact) => artifact.name === current)) {
          return current;
        }
        const preferred = nextArtifacts.find((artifact) => artifact.name === 'prd.md') || nextArtifacts[0];
        return preferred.name;
      });
    } catch (error) {
      setArtifactError(friendlyError(error, 'Could not load artifacts.'));
    } finally {
      setArtifactLoading(false);
    }
  }, []);

  const loadEvaluation = useCallback(async (taskId: string) => {
    setEvaluationLoading(true);
    setEvaluationError(null);
    try {
      setEvaluation(await getEvaluation(taskId));
    } catch {
      setEvaluation(null);
      setEvaluationError('Evaluation is not available yet.');
    } finally {
      setEvaluationLoading(false);
    }
  }, []);

  const connectEvents = useCallback(
    (taskId: string) => {
      socketRef.current?.close();
      setWebsocketStatus('CONNECTING');
      const socket = new WebSocket(buildTaskEventsWebSocketUrl(taskId));
      socketRef.current = socket;

      socket.onopen = () => {
        if (socketRef.current === socket) {
          setWebsocketStatus('CONNECTED');
        }
      };
      socket.onmessage = async (message) => {
        if (socketRef.current !== socket) {
          return;
        }
        const payload = JSON.parse(message.data) as TaskWebSocketMessage;
        if (payload.type === 'event') {
          setEvents((current) => uniqueEvents([...current, payload.data]));
        }
        if (payload.type === 'task_finished') {
          setWebsocketStatus('FINISHED');
          await Promise.all([refreshSelectedTask(taskId), refreshTasks(), loadArtifacts(taskId), loadEvaluation(taskId)]);
        }
        if (payload.type === 'error') {
          setWebsocketStatus('ERROR');
        }
      };
      socket.onerror = () => {
        if (socketRef.current === socket) {
          setWebsocketStatus('ERROR');
        }
      };
      socket.onclose = () => {
        if (socketRef.current === socket) {
          setWebsocketStatus((current) => (current === 'FINISHED' ? 'FINISHED' : 'DISCONNECTED'));
        }
      };
    },
    [loadArtifacts, loadEvaluation, refreshSelectedTask, refreshTasks],
  );

  const selectTask = useCallback(
    async (taskId: string) => {
      socketRef.current?.close();
      setSelectedArtifact(undefined);
      setArtifactContent(undefined);
      setEvaluation(null);
      setWebsocketStatus('IDLE');
      try {
        const meta = await refreshSelectedTask(taskId);
        await Promise.all([loadEvents(taskId), loadArtifacts(taskId), loadEvaluation(taskId)]);
        if (meta.status === 'RUNNING') {
          connectEvents(taskId);
        }
      } catch (error) {
        setTaskListError(friendlyError(error, 'Could not load the selected task.'));
      }
    },
    [connectEvents, loadArtifacts, loadEvaluation, loadEvents, refreshSelectedTask],
  );

  async function handleCreateTask(task: string, model: string, mock: boolean) {
    setTaskLoading(true);
    try {
      const created = await createTask({ task, model, mock, run_async: true });
      await refreshTasks();
      await selectTask(created.task_id);
    } finally {
      setTaskLoading(false);
    }
  }

  useEffect(() => {
    getHealth()
      .then(() => setBackendStatus('OK'))
      .catch(() => setBackendStatus('OFFLINE'));
    refreshTasks();
    return () => socketRef.current?.close();
  }, [refreshTasks]);

  useEffect(() => {
    if (!selectedTask || !selectedArtifact) {
      return;
    }
    setArtifactLoading(true);
    setArtifactError(null);
    getArtifact(selectedTask.task_id, selectedArtifact)
      .then((artifact) => setArtifactContent(artifact.content))
      .catch((error) => setArtifactError(friendlyError(error, 'Could not load artifact.')))
      .finally(() => setArtifactLoading(false));
  }, [selectedArtifact, selectedTask]);

  const left = (
    <>
      <TaskCreator onCreate={handleCreateTask} loading={taskLoading} />
      <TaskList
        tasks={tasks}
        selectedTaskId={selectedTask?.task_id}
        loading={taskListLoading}
        error={taskListError}
        onSelect={selectTask}
        onRefresh={refreshTasks}
      />
    </>
  );

  const center = (
    <>
      <AgentBoard events={events} hasSelectedTask={Boolean(selectedTask)} />
      <EventTimeline events={events} />
    </>
  );

  const right = (
    <>
      <ArtifactExplorer
        artifacts={artifacts}
        selectedArtifact={selectedArtifact}
        loading={artifactLoading}
        error={artifactError}
        onSelect={setSelectedArtifact}
      />
      <ArtifactViewer artifactName={selectedArtifact} content={artifactContent} loading={artifactLoading} error={artifactError} />
      <EvaluationPanel evaluation={evaluation} loading={evaluationLoading} error={evaluationError} />
    </>
  );

  return (
    <Layout
      backendStatus={backendStatus}
      currentTaskStatus={selectedTask?.status}
      websocketStatus={websocketStatus}
      left={left}
      center={center}
      right={right}
    />
  );
}

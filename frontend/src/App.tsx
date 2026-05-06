import { useCallback, useEffect, useRef, useState } from 'react';
import {
  buildTaskEventsWebSocketUrl,
  createTask,
  createFeedback,
  getArtifact,
  getArtifactVersion,
  getEvaluation,
  getHealth,
  getTask,
  getTaskEvents,
  listArtifactVersions,
  listArtifacts,
  listFeedback,
  listRevisions,
  listTasks,
  requestRevision,
} from './api/client';
import { AgentBoard } from './components/AgentBoard';
import { ArtifactExplorer } from './components/ArtifactExplorer';
import { ArtifactVersions } from './components/ArtifactVersions';
import { ArtifactViewer } from './components/ArtifactViewer';
import { EvaluationPanel } from './components/EvaluationPanel';
import { EventTimeline } from './components/EventTimeline';
import { HumanControlPanel } from './components/HumanControlPanel';
import { Layout } from './components/Layout';
import { RevisionHistory } from './components/RevisionHistory';
import { TaskCreator } from './components/TaskCreator';
import { TaskList } from './components/TaskList';
import type {
  AgentEvent,
  ArtifactInfo,
  ArtifactVersionInfo,
  EvaluationResult,
  HumanFeedback,
  RevisionRecord,
  TaskMeta,
  TaskWebSocketMessage,
} from './types';

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
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>();
  const [artifactContent, setArtifactContent] = useState<string | undefined>();
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [feedback, setFeedback] = useState<HumanFeedback[]>([]);
  const [revisions, setRevisions] = useState<RevisionRecord[]>([]);
  const [versions, setVersions] = useState<ArtifactVersionInfo[]>([]);
  const [taskLoading, setTaskLoading] = useState(false);
  const [taskListLoading, setTaskListLoading] = useState(false);
  const [artifactLoading, setArtifactLoading] = useState(false);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [controlLoading, setControlLoading] = useState(false);
  const [revisionLoading, setRevisionLoading] = useState(false);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [taskListError, setTaskListError] = useState<string | null>(null);
  const [artifactError, setArtifactError] = useState<string | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);
  const [controlError, setControlError] = useState<string | null>(null);
  const [revisionError, setRevisionError] = useState<string | null>(null);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [websocketStatus, setWebsocketStatus] = useState('IDLE');
  const socketRef = useRef<WebSocket | null>(null);
  const backendStatusRef = useRef('CHECKING');

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

  const loadFeedback = useCallback(async (taskId: string) => {
    try {
      setFeedback(await listFeedback(taskId));
    } catch (error) {
      setControlError(friendlyError(error, 'Could not load human feedback.'));
    }
  }, []);

  const loadRevisions = useCallback(async (taskId: string) => {
    setRevisionLoading(true);
    setRevisionError(null);
    try {
      setRevisions(await listRevisions(taskId));
    } catch (error) {
      setRevisionError(friendlyError(error, 'Could not load revision history.'));
    } finally {
      setRevisionLoading(false);
    }
  }, []);

  const loadVersions = useCallback(async (taskId: string, artifactName?: string) => {
    if (!artifactName) {
      setVersions([]);
      return;
    }
    setVersionsLoading(true);
    setVersionsError(null);
    try {
      setVersions(await listArtifactVersions(taskId, artifactName));
    } catch (error) {
      setVersionsError(friendlyError(error, 'Could not load artifact versions.'));
    } finally {
      setVersionsLoading(false);
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
          await Promise.all([
            refreshSelectedTask(taskId),
            refreshTasks(),
            loadArtifacts(taskId),
            loadEvaluation(taskId),
            loadFeedback(taskId),
            loadRevisions(taskId),
            loadVersions(taskId, selectedArtifact),
          ]);
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
    [loadArtifacts, loadEvaluation, loadFeedback, loadRevisions, loadVersions, refreshSelectedTask, refreshTasks, selectedArtifact],
  );

  const selectTask = useCallback(
    async (taskId: string) => {
      socketRef.current?.close();
      setSelectedArtifact(undefined);
      setSelectedVersion(undefined);
      setArtifactContent(undefined);
      setEvaluation(null);
      setFeedback([]);
      setRevisions([]);
      setVersions([]);
      setWebsocketStatus('IDLE');
      try {
        const meta = await refreshSelectedTask(taskId);
        await Promise.all([
          loadEvents(taskId),
          loadArtifacts(taskId),
          loadEvaluation(taskId),
          loadFeedback(taskId),
          loadRevisions(taskId),
        ]);
        if (meta.status === 'RUNNING') {
          connectEvents(taskId);
        }
      } catch (error) {
        setTaskListError(friendlyError(error, 'Could not load the selected task.'));
      }
    },
    [connectEvents, loadArtifacts, loadEvaluation, loadEvents, loadFeedback, loadRevisions, refreshSelectedTask],
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

  async function handleSaveFeedback(targetAgent: string, targetArtifact: string, content: string) {
    if (!selectedTask) {
      return;
    }
    setControlLoading(true);
    setControlError(null);
    try {
      await createFeedback(selectedTask.task_id, { target_agent: targetAgent, target_artifact: targetArtifact, content });
      await Promise.all([loadFeedback(selectedTask.task_id), loadEvents(selectedTask.task_id)]);
    } catch (error) {
      setControlError(friendlyError(error, 'Could not save human feedback.'));
    } finally {
      setControlLoading(false);
    }
  }

  async function handleRunRevision(feedbackId: string, rerunDownstream: boolean) {
    if (!selectedTask) {
      return;
    }
    setControlLoading(true);
    setControlError(null);
    try {
      const revision = await requestRevision(selectedTask.task_id, {
        feedback_id: feedbackId,
        rerun_downstream: rerunDownstream,
        run_async: true,
      });
      setWebsocketStatus(`REVISION_${revision.status}`);
      connectEvents(selectedTask.task_id);
      await Promise.all([refreshSelectedTask(selectedTask.task_id), loadFeedback(selectedTask.task_id), loadRevisions(selectedTask.task_id)]);
    } catch (error) {
      setControlError(friendlyError(error, 'Could not start revision.'));
    } finally {
      setControlLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    async function checkBackend() {
      try {
        await getHealth();
        if (!active) {
          return;
        }
        const wasOffline = backendStatusRef.current !== 'OK';
        backendStatusRef.current = 'OK';
        setBackendStatus('OK');
        if (wasOffline) {
          refreshTasks();
        }
      } catch {
        if (!active) {
          return;
        }
        backendStatusRef.current = 'OFFLINE';
        setBackendStatus('OFFLINE');
      }
    }

    checkBackend();
    const intervalId = window.setInterval(checkBackend, 3000);
    return () => {
      active = false;
      window.clearInterval(intervalId);
      socketRef.current?.close();
    };
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
    setSelectedVersion(undefined);
    loadVersions(selectedTask.task_id, selectedArtifact);
  }, [loadVersions, selectedArtifact, selectedTask]);

  useEffect(() => {
    if (!selectedTask || !selectedArtifact || !selectedVersion) {
      return;
    }
    setArtifactLoading(true);
    setArtifactError(null);
    getArtifactVersion(selectedTask.task_id, selectedArtifact, selectedVersion)
      .then((artifact) => setArtifactContent(artifact.content))
      .catch((error) => setArtifactError(friendlyError(error, 'Could not load artifact version.')))
      .finally(() => setArtifactLoading(false));
  }, [selectedArtifact, selectedTask, selectedVersion]);

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
      <ArtifactVersions
        artifactName={selectedArtifact}
        versions={versions}
        selectedVersion={selectedVersion}
        loading={versionsLoading}
        error={versionsError}
        onSelectVersion={setSelectedVersion}
        onShowCurrent={() => {
          setSelectedVersion(undefined);
          if (selectedTask && selectedArtifact) {
            getArtifact(selectedTask.task_id, selectedArtifact).then((artifact) => setArtifactContent(artifact.content));
          }
        }}
      />
      <HumanControlPanel
        artifacts={artifacts}
        selectedArtifact={selectedArtifact}
        feedback={feedback}
        disabled={!selectedTask || selectedTask.status === 'RUNNING'}
        loading={controlLoading}
        error={controlError}
        onSaveFeedback={handleSaveFeedback}
        onRunRevision={handleRunRevision}
      />
      <RevisionHistory revisions={revisions} loading={revisionLoading} error={revisionError} />
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

import type { TaskMeta } from '../types';
import { formatDate, shortTaskId } from '../utils/format';
import { StatusBadge } from './StatusBadge';

interface TaskListProps {
  tasks: TaskMeta[];
  selectedTaskId?: string;
  loading: boolean;
  error?: string | null;
  onSelect: (taskId: string) => void;
  onRefresh: () => void;
}

export function TaskList({ tasks, selectedTaskId, loading, error, onSelect, onRefresh }: TaskListProps) {
  return (
    <section className="panel task-list-panel">
      <div className="panel-header">
        <h2>Previous Tasks</h2>
        <button className="secondary-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
      </div>
      {loading && <p className="muted">Loading tasks...</p>}
      {error && <p className="error-text">{error}</p>}
      <div className="task-list">
        {tasks.map((task) => (
          <button
            className={`task-item ${selectedTaskId === task.task_id ? 'selected' : ''}`}
            key={task.task_id}
            type="button"
            onClick={() => onSelect(task.task_id)}
          >
            <div className="task-item-top">
              <strong>{shortTaskId(task.task_id)}</strong>
              <StatusBadge status={task.status} />
            </div>
            <p>{task.task_input_preview}</p>
            <div className="task-meta-row">
              <span>{task.mock ? 'mock' : 'real'}</span>
              <span>{task.model}</span>
            </div>
            <span className="muted">{formatDate(task.created_at)}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

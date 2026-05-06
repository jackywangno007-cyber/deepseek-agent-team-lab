import type { ImprovementHistoryRecord } from '../types';
import { formatDate, shortTaskId } from '../utils/format';
import { StatusBadge } from './StatusBadge';

interface ImprovementHistoryProps {
  history: ImprovementHistoryRecord[];
  loading: boolean;
  error?: string | null;
}

export function ImprovementHistory({ history, loading, error }: ImprovementHistoryProps) {
  return (
    <section className="panel improvement-history-panel">
      <div className="panel-header">
        <h2>Improvement History</h2>
        <span className="muted">{history.length} actions</span>
      </div>
      {loading && <p className="muted">Loading improvement history...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && history.length === 0 && <p className="muted">No improvement actions yet.</p>}
      <div className="revision-list">
        {history.map((item) => (
          <article className="revision-item" key={item.improvement_id}>
            <div className="task-item-top">
              <strong>{shortTaskId(item.improvement_id)}</strong>
              <StatusBadge status={item.status} />
            </div>
            <p>
              {item.action}: {item.responsible_agent} {'->'} <strong>{item.target_artifact}</strong>
            </p>
            {item.feedback_id && <p className="muted">Feedback: {shortTaskId(item.feedback_id)}</p>}
            {item.revision_id && <p className="muted">Revision: {shortTaskId(item.revision_id)}</p>}
            {item.reason && <p className="muted">Reason: {item.reason}</p>}
            <p className="muted">Created: {formatDate(item.created_at)}</p>
            {item.completed_at && <p className="muted">Completed: {formatDate(item.completed_at)}</p>}
            {item.error && <p className="error-text">{item.error}</p>}
          </article>
        ))}
      </div>
    </section>
  );
}

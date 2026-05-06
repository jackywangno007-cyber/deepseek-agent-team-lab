import type { RevisionRecord } from '../types';
import { formatDate, shortTaskId } from '../utils/format';
import { StatusBadge } from './StatusBadge';

interface RevisionHistoryProps {
  revisions: RevisionRecord[];
  loading: boolean;
  error?: string | null;
}

export function RevisionHistory({ revisions, loading, error }: RevisionHistoryProps) {
  return (
    <section className="panel revision-panel">
      <div className="panel-header">
        <h2>Revision History</h2>
        <span className="muted">{revisions.length} revisions</span>
      </div>
      {loading && <p className="muted">Loading revisions...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && revisions.length === 0 && <p className="muted">No revisions yet.</p>}
      <div className="revision-list">
        {revisions.map((revision) => (
          <article className="revision-item" key={revision.revision_id}>
            <div className="task-item-top">
              <strong>{shortTaskId(revision.revision_id)}</strong>
              <StatusBadge status={revision.status} />
            </div>
            <p>
              {revision.target_agent} revised <strong>{revision.target_artifact}</strong>
            </p>
            <p className="muted">Downstream rerun: {String(revision.rerun_downstream)}</p>
            {revision.backup_artifact && <p className="muted">Backup: {revision.backup_artifact}</p>}
            <p className="muted">Created: {formatDate(revision.created_at)}</p>
            {revision.completed_at && <p className="muted">Completed: {formatDate(revision.completed_at)}</p>}
            {revision.error && <p className="error-text">{revision.error}</p>}
          </article>
        ))}
      </div>
    </section>
  );
}

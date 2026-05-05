import type { EvaluationResult } from '../types';
import { StatusBadge } from './StatusBadge';

interface EvaluationPanelProps {
  evaluation?: EvaluationResult | null;
  loading: boolean;
  error?: string | null;
}

const fields: Array<keyof EvaluationResult> = [
  'artifacts_complete',
  'events_complete',
  'review_score_found',
  'final_summary_found',
];

export function EvaluationPanel({ evaluation, loading, error }: EvaluationPanelProps) {
  return (
    <section className="panel evaluation-panel">
      <div className="panel-header">
        <h2>Evaluation</h2>
        {evaluation && <StatusBadge status={evaluation.passed ? 'PASSED' : 'FAILED'} />}
      </div>
      {loading && <p className="muted">Loading evaluation...</p>}
      {error && <p className="muted">{error}</p>}
      {!loading && !error && !evaluation && <p className="muted">Evaluation is not available yet.</p>}
      {evaluation && (
        <dl className="evaluation-list">
          {fields.map((field) => (
            <div key={field}>
              <dt>{field}</dt>
              <dd>{String(Boolean(evaluation[field]))}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

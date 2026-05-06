import type { EvaluationCompareResult } from '../types';
import { StatusBadge } from './StatusBadge';

interface EvaluationComparePanelProps {
  compare: EvaluationCompareResult | null;
  loading: boolean;
  error?: string | null;
}

export function EvaluationComparePanel({ compare, loading, error }: EvaluationComparePanelProps) {
  return (
    <section className="panel evaluation-compare-panel">
      <div className="panel-header">
        <h2>Evaluation Compare</h2>
        {compare && <StatusBadge status={compare.changed ? 'changed' : 'unchanged'} />}
      </div>
      {loading && <p className="muted">Loading evaluation comparison...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !compare && <p className="muted">No evaluation comparison yet.</p>}
      {compare && (
        <>
          <p className="muted">{compare.summary}</p>
          <div className="compare-grid">
            <div>
              <h3>Before</h3>
              <pre>{JSON.stringify(compare.before, null, 2)}</pre>
            </div>
            <div>
              <h3>After</h3>
              <pre>{JSON.stringify(compare.after, null, 2)}</pre>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

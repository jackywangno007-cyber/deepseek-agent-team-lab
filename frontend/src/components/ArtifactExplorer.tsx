import type { ArtifactInfo } from '../types';
import { formatBytes, formatDate } from '../utils/format';

interface ArtifactExplorerProps {
  artifacts: ArtifactInfo[];
  selectedArtifact?: string;
  loading: boolean;
  error?: string | null;
  onSelect: (artifactName: string) => void;
}

const preferredOrder = [
  'prd.md',
  'architecture.md',
  'frontend_plan.md',
  'api_design.md',
  'test_plan.md',
  'review_report.md',
  'final_summary.md',
  'evaluation.json',
  'events.jsonl',
  'task_meta.json',
  'task_plan.json',
  'task_input.md',
];

function sortArtifacts(artifacts: ArtifactInfo[]): ArtifactInfo[] {
  return [...artifacts].sort((left, right) => {
    const leftIndex = preferredOrder.indexOf(left.name);
    const rightIndex = preferredOrder.indexOf(right.name);
    if (leftIndex !== -1 || rightIndex !== -1) {
      return (leftIndex === -1 ? 999 : leftIndex) - (rightIndex === -1 ? 999 : rightIndex);
    }
    return left.name.localeCompare(right.name);
  });
}

export function ArtifactExplorer({ artifacts, selectedArtifact, loading, error, onSelect }: ArtifactExplorerProps) {
  return (
    <section className="panel artifact-panel">
      <div className="panel-header">
        <h2>Artifacts</h2>
        <span className="muted">{artifacts.length} files</span>
      </div>
      {loading && <p className="muted">Loading artifacts...</p>}
      {error && <p className="error-text">{error}</p>}
      <div className="artifact-list">
        {sortArtifacts(artifacts).map((artifact) => (
          <button
            className={`artifact-item ${selectedArtifact === artifact.name ? 'selected' : ''}`}
            key={artifact.name}
            type="button"
            onClick={() => onSelect(artifact.name)}
          >
            <strong>{artifact.name}</strong>
            <span>{formatBytes(artifact.size_bytes)}</span>
            <span className="muted">{formatDate(artifact.modified_at)}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

import type { ArtifactVersionInfo } from '../types';
import { formatBytes, formatDate } from '../utils/format';

interface ArtifactVersionsProps {
  artifactName?: string;
  versions: ArtifactVersionInfo[];
  selectedVersion?: string;
  loading: boolean;
  error?: string | null;
  onSelectVersion: (versionName: string) => void;
  onShowCurrent: () => void;
}

export function ArtifactVersions({
  artifactName,
  versions,
  selectedVersion,
  loading,
  error,
  onSelectVersion,
  onShowCurrent,
}: ArtifactVersionsProps) {
  return (
    <section className="panel versions-panel">
      <div className="panel-header">
        <h2>Artifact Versions</h2>
        <span className="muted">{artifactName || 'No artifact selected'}</span>
      </div>
      {loading && <p className="muted">Loading versions...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && versions.length === 0 && <p className="muted">No previous versions yet.</p>}
      {versions.length > 0 && (
        <button type="button" className="secondary-button" onClick={onShowCurrent}>
          Show current artifact
        </button>
      )}
      <div className="artifact-list">
        {versions.map((version) => (
          <button
            className={`artifact-item ${selectedVersion === version.name ? 'selected' : ''}`}
            key={version.name}
            type="button"
            onClick={() => onSelectVersion(version.name)}
          >
            <strong>{version.name}</strong>
            <span>{formatBytes(version.size_bytes)}</span>
            <span className="muted">{formatDate(version.created_at)}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

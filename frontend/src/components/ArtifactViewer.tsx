interface ArtifactViewerProps {
  artifactName?: string;
  content?: string;
  loading: boolean;
  error?: string | null;
}

export function ArtifactViewer({ artifactName, content, loading, error }: ArtifactViewerProps) {
  return (
    <section className="panel viewer-panel">
      <div className="panel-header">
        <h2>Artifact Viewer</h2>
        <span className="muted">{artifactName || 'No artifact selected'}</span>
      </div>
      {loading && <p className="muted">Loading artifact...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && !content && <p className="muted">Select an artifact to inspect its content.</p>}
      {!loading && !error && content && <pre className="artifact-content">{content}</pre>}
    </section>
  );
}

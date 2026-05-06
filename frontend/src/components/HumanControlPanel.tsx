import { FormEvent, useEffect, useMemo, useState } from 'react';
import type { ArtifactInfo, HumanFeedback } from '../types';

const artifactOwners: Record<string, string> = {
  'prd.md': 'ProductAgent',
  'architecture.md': 'ArchitectAgent',
  'frontend_plan.md': 'FrontendAgent',
  'api_design.md': 'BackendAgent',
  'test_plan.md': 'TestAgent',
  'review_report.md': 'ReviewerAgent',
  'final_summary.md': 'ManagerAgent',
};

interface HumanControlPanelProps {
  artifacts: ArtifactInfo[];
  selectedArtifact?: string;
  feedback: HumanFeedback[];
  disabled: boolean;
  loading: boolean;
  error?: string | null;
  onSaveFeedback: (targetAgent: string, targetArtifact: string, content: string) => Promise<void>;
  onRunRevision: (feedbackId: string, rerunDownstream: boolean) => Promise<void>;
}

export function HumanControlPanel({
  artifacts,
  selectedArtifact,
  feedback,
  disabled,
  loading,
  error,
  onSaveFeedback,
  onRunRevision,
}: HumanControlPanelProps) {
  const artifactNames = useMemo(
    () => artifacts.map((artifact) => artifact.name).filter((name) => Boolean(artifactOwners[name])),
    [artifacts],
  );
  const [targetArtifact, setTargetArtifact] = useState(selectedArtifact || 'prd.md');
  const [targetAgent, setTargetAgent] = useState(artifactOwners[targetArtifact] || 'ProductAgent');
  const [content, setContent] = useState('');
  const [selectedFeedbackId, setSelectedFeedbackId] = useState('');
  const [rerunDownstream, setRerunDownstream] = useState(true);
  const pendingFeedback = feedback.filter((item) => item.status === 'PENDING');

  useEffect(() => {
    if (selectedArtifact && artifactOwners[selectedArtifact]) {
      setTargetArtifact(selectedArtifact);
      setTargetAgent(artifactOwners[selectedArtifact]);
    }
  }, [selectedArtifact]);

  useEffect(() => {
    setTargetAgent(artifactOwners[targetArtifact] || 'ProductAgent');
  }, [targetArtifact]);

  useEffect(() => {
    if (!selectedFeedbackId && pendingFeedback.length > 0) {
      setSelectedFeedbackId(pendingFeedback[0].feedback_id);
    }
  }, [pendingFeedback, selectedFeedbackId]);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!content.trim()) {
      return;
    }
    await onSaveFeedback(targetAgent, targetArtifact, content.trim());
    setContent('');
  }

  async function handleRunRevision() {
    if (!selectedFeedbackId) {
      return;
    }
    await onRunRevision(selectedFeedbackId, rerunDownstream);
  }

  return (
    <section className="panel human-panel">
      <div className="panel-header">
        <h2>Human Control</h2>
        <span className="muted">Feedback first, revision second</span>
      </div>
      <form className="task-form" onSubmit={handleSave}>
        <label>
          Target artifact
          <select value={targetArtifact} onChange={(event) => setTargetArtifact(event.target.value)} disabled={disabled}>
            {artifactNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Target agent
          <select value={targetAgent} onChange={(event) => setTargetAgent(event.target.value)} disabled={disabled}>
            {Object.entries(artifactOwners).map(([artifact, agent]) => (
              <option key={artifact} value={agent}>
                {agent}
              </option>
            ))}
          </select>
        </label>
        <label>
          Feedback
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            rows={4}
            placeholder="Describe the concrete artifact change you want."
            disabled={disabled}
          />
        </label>
        <button type="submit" disabled={disabled || loading || !content.trim()}>
          Save feedback
        </button>
      </form>
      <div className="revision-runner">
        <label>
          Saved feedback
          <select value={selectedFeedbackId} onChange={(event) => setSelectedFeedbackId(event.target.value)} disabled={disabled}>
            {pendingFeedback.length === 0 && <option value="">No pending feedback</option>}
            {pendingFeedback.map((item) => (
              <option key={item.feedback_id} value={item.feedback_id}>
                {item.target_artifact} - {item.content.slice(0, 50)}
              </option>
            ))}
          </select>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={rerunDownstream}
            onChange={(event) => setRerunDownstream(event.target.checked)}
            disabled={disabled}
          />
          Rerun downstream agents
        </label>
        <button type="button" onClick={handleRunRevision} disabled={disabled || loading || !selectedFeedbackId}>
          Run revision
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}
      <p className="muted">Artifact versions are backed up before revision overwrites any file.</p>
    </section>
  );
}

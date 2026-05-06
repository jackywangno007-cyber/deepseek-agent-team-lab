import { useState } from 'react';
import type { ImprovementSuggestion } from '../types';
import { formatDate, shortTaskId } from '../utils/format';
import { StatusBadge } from './StatusBadge';

interface ImprovementSuggestionsProps {
  suggestions: ImprovementSuggestion[];
  loading: boolean;
  disabled: boolean;
  error?: string | null;
  onGenerate: () => Promise<void>;
  onApprove: (suggestionId: string, editedFeedback: string, rerunDownstream: boolean) => Promise<void>;
  onReject: (suggestionId: string, reason: string) => Promise<void>;
}

export function ImprovementSuggestions({
  suggestions,
  loading,
  disabled,
  error,
  onGenerate,
  onApprove,
  onReject,
}: ImprovementSuggestionsProps) {
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({});
  const [rerunDownstream, setRerunDownstream] = useState<Record<string, boolean>>({});

  return (
    <section className="panel improvement-panel">
      <div className="panel-header">
        <h2>Improvement Suggestions</h2>
        <button className="secondary-button" type="button" onClick={onGenerate} disabled={disabled || loading}>
          Generate
        </button>
      </div>
      {loading && <p className="muted">Working on suggestions...</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && suggestions.length === 0 && <p className="muted">No suggestions yet. Generate them after a task completes.</p>}
      <div className="improvement-list">
        {suggestions.map((suggestion) => {
          const feedback = edits[suggestion.suggestion_id] ?? suggestion.proposed_feedback;
          const canAct = !disabled && !loading && suggestion.status === 'PENDING';
          return (
            <article className="improvement-item" key={suggestion.suggestion_id}>
              <div className="task-item-top">
                <strong>{shortTaskId(suggestion.suggestion_id)}</strong>
                <StatusBadge status={suggestion.status} />
              </div>
              <p>
                <strong>{suggestion.issue_summary}</strong>
              </p>
              <p className="muted">
                {suggestion.responsible_agent} {'->'} {suggestion.target_artifact} | {suggestion.severity}
              </p>
              <p className="muted">{suggestion.reason}</p>
              <label>
                Proposed feedback
                <textarea
                  value={feedback}
                  rows={4}
                  disabled={!canAct}
                  onChange={(event) => setEdits((current) => ({ ...current, [suggestion.suggestion_id]: event.target.value }))}
                />
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={rerunDownstream[suggestion.suggestion_id] ?? true}
                  disabled={!canAct}
                  onChange={(event) => setRerunDownstream((current) => ({ ...current, [suggestion.suggestion_id]: event.target.checked }))}
                />
                Rerun downstream agents
              </label>
              <div className="action-row">
                <button type="button" disabled={!canAct || !feedback.trim()} onClick={() => onApprove(suggestion.suggestion_id, feedback.trim(), rerunDownstream[suggestion.suggestion_id] ?? true)}>
                  Approve
                </button>
              </div>
              <label>
                Reject reason
                <input
                  value={rejectReasons[suggestion.suggestion_id] || ''}
                  disabled={!canAct}
                  placeholder="Optional reason"
                  onChange={(event) => setRejectReasons((current) => ({ ...current, [suggestion.suggestion_id]: event.target.value }))}
                />
              </label>
              <button type="button" className="secondary-button" disabled={!canAct} onClick={() => onReject(suggestion.suggestion_id, rejectReasons[suggestion.suggestion_id] || '')}>
                Reject
              </button>
              <p className="muted">Created: {formatDate(suggestion.created_at)}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

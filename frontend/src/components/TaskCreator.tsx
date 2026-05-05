import { FormEvent, useState } from 'react';

interface TaskCreatorProps {
  onCreate: (task: string, model: string, mock: boolean) => Promise<void>;
  loading: boolean;
}

export function TaskCreator({ onCreate, loading }: TaskCreatorProps) {
  const [task, setTask] = useState('Design an MVP for a student course management system');
  const [model, setModel] = useState('deepseek-v4-flash');
  const [mock, setMock] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!task.trim()) {
      setError('Please enter a project requirement.');
      return;
    }
    try {
      await onCreate(task.trim(), model.trim() || 'deepseek-v4-flash', mock);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Task creation failed.');
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Create Task</h2>
      </div>
      <form className="task-form" onSubmit={handleSubmit}>
        <label>
          Requirement
          <textarea value={task} onChange={(event) => setTask(event.target.value)} rows={6} />
        </label>
        <label>
          Model
          <input value={model} onChange={(event) => setModel(event.target.value)} />
        </label>
        <label className="checkbox-row">
          <input type="checkbox" checked={mock} onChange={(event) => setMock(event.target.checked)} />
          Mock mode
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Starting...' : 'Run agent team'}
        </button>
      </form>
    </section>
  );
}

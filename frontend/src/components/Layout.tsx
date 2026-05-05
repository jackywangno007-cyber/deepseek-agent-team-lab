import type { ReactNode } from 'react';
import { StatusBadge } from './StatusBadge';

interface LayoutProps {
  backendStatus: string;
  currentTaskStatus?: string;
  websocketStatus: string;
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
}

export function Layout({ backendStatus, currentTaskStatus, websocketStatus, left, center, right }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <h1>DeepSeek Agent Team Lab</h1>
          <p>Local AgentOps dashboard for artifact-driven collaboration</p>
        </div>
        <div className="topbar-status">
          <div>
            <span className="muted">Backend</span>
            <StatusBadge status={backendStatus} />
          </div>
          <div>
            <span className="muted">Task</span>
            <StatusBadge status={currentTaskStatus || 'IDLE'} />
          </div>
          <div>
            <span className="muted">Events</span>
            <StatusBadge status={websocketStatus} />
          </div>
        </div>
      </header>
      <main className="dashboard-grid">
        <aside className="sidebar">{left}</aside>
        <section className="main-column">{center}</section>
        <aside className="right-column">{right}</aside>
      </main>
    </div>
  );
}

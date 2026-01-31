import React from 'react';

export default function Dashboard({ migrationState, agentColors }) {
  const { status, currentAgent, progress, components } = migrationState;

  const completedCount = components.filter(c => c.status === 'complete').length;
  const failedCount = components.filter(c => c.status === 'failed').length;
  const pendingCount = components.filter(c => c.status === 'pending').length;

  const stats = [
    { label: 'Total Components', value: components.length, color: '#94a3b8' },
    { label: 'Completed', value: completedCount, color: '#34d399' },
    { label: 'Failed', value: failedCount, color: '#f87171' },
    { label: 'Pending', value: pendingCount, color: '#fbbf24' },
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2 className="dashboard-title">Migration Overview</h2>
        <div className={`status-badge status-${status}`}>
          {status.toUpperCase()}
        </div>
      </div>

      <div className="stats-grid">
        {stats.map(stat => (
          <div key={stat.label} className="stat-card" style={{ '--stat-color': stat.color }}>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      {currentAgent && (
        <div className="current-agent-card" style={{ '--agent-color': agentColors[currentAgent] }}>
          <div className="agent-indicator">
            <span className="agent-pulse" />
            <span className="agent-name">{currentAgent.charAt(0).toUpperCase() + currentAgent.slice(1)} Agent</span>
          </div>
          <div className="agent-status">
            {status === 'running' ? 'Currently processing...' : status === 'complete' ? 'Migration complete!' : 'Waiting...'}
          </div>
        </div>
      )}
    </div>
  );
}

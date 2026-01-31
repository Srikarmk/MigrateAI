import React from 'react';

export default function ProgressView({ status, currentAgent, progress, components, agentColors }) {
  const completedCount = components.filter(c => c.status === 'complete').length;
  const totalCount = components.length;

  const agents = [
    { id: 'ingest', label: 'Ingest', icon: '📥', description: 'Parsing codebase structure' },
    { id: 'analyze', label: 'Analyze', icon: '🔬', description: 'Mapping dependencies' },
    { id: 'plan', label: 'Plan', icon: '📋', description: 'Creating migration strategy' },
    { id: 'execute', label: 'Execute', icon: '⚡', description: 'Refactoring code' },
    { id: 'test', label: 'Test', icon: '🧪', description: 'Running test suite' },
    { id: 'verify', label: 'Verify', icon: '👁️', description: 'Visual verification' },
    { id: 'review', label: 'Review', icon: '📝', description: 'Code quality check' },
    { id: 'document', label: 'Document', icon: '📖', description: 'Generating docs' },
  ];

  const currentAgentIndex = agents.findIndex(a => a.id === currentAgent);
  
  // Calculate progress percentage, ensuring it's between 0 and 100
  // Use raw progress value directly (should be 0-1)
  const rawProgress = progress || 0;
  const progressPercent = Math.min(Math.max(rawProgress * 100, 0), 100);

  return (
    <div className="progress-view">
      <div className="progress-header-section">
        <div className="progress-title">
          <h2>Migration Progress</h2>
          <span className={`migration-status status-${status}`}>
            {status === 'running' && <span className="status-pulse" />}
            {status === 'running' && currentAgent 
              ? `${currentAgent.charAt(0).toUpperCase() + currentAgent.slice(1)} Agent`
              : status === 'failed' 
                ? '❌ Failed'
                : status === 'complete'
                  ? '✅ Complete'
                  : status === 'stopped'
                    ? '⏹ Stopped'
                    : status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        </div>
        
        {totalCount > 0 && (
          <div className="component-progress">
            <div className="component-count">
              <span className="count-completed">{completedCount}</span>
              <span className="count-separator">/</span>
              <span className="count-total">{totalCount}</span>
            </div>
            <span className="count-label">components migrated</span>
          </div>
        )}
      </div>

      <div className="progress-bar-section">
        <div className="progress-bar-wrapper">
          <div className="main-progress-bar">
            <div 
              className="progress-fill"
              style={{ 
                width: `${progressPercent}%`,
                background: currentAgent ? agentColors[currentAgent] : '#34d399',
              }}
            />
            <div className="progress-glow" style={{ left: `${progressPercent}%` }} />
          </div>
        <div className="progress-percentage">
          {Math.round(progressPercent)}%
        </div>
        </div>
      </div>

      <div className="agents-timeline">
        {agents.map((agent, index) => {
          const isActive = currentAgent === agent.id;
          // Calculate if agent is complete based on progress and current agent
          // Progress thresholds: ingest=0.2, analyze=0.4, plan=0.5, execute=0.7, test=0.8, verify=0.9, review=0.95, document=1.0
          const progressThresholds = [0.2, 0.4, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0];
          const agentProgressThreshold = progressThresholds[index] || (index + 1) * 0.125;
          
          const isComplete = status === 'complete' || 
                           (currentAgentIndex > index) ||
                           (progress >= agentProgressThreshold && currentAgentIndex !== index);
          const isFuture = !isActive && !isComplete;

          return (
            <div 
              key={agent.id}
              className={`agent-step ${isActive ? 'active' : ''} ${isComplete ? 'complete' : ''} ${isFuture ? 'future' : ''}`}
              style={{ '--agent-color': agentColors[agent.id] }}
            >
              <div className="agent-node">
                <div className="node-circle">
                  {isComplete ? (
                    <span className="check-icon">✓</span>
                  ) : (
                    <span className="agent-icon">{agent.icon}</span>
                  )}
                </div>
                {isActive && <div className="active-ring" />}
              </div>
              <div className="agent-info">
                <span className="agent-label">{agent.label}</span>
                {isActive && (
                  <span className="agent-description">{agent.description}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {status === 'idle' && (
        <div className="idle-message">
          <div className="idle-icon">🚀</div>
          <p>Ready to start migration</p>
          <p className="idle-hint">Enter a repository URL above to begin</p>
        </div>
      )}

      {status === 'complete' && (
        <div className="complete-message-compact">
          <div className="complete-icon">🎉</div>
          <p>Migration Complete! {completedCount} components migrated</p>
        </div>
      )}
    </div>
  );
}

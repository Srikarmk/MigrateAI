import React, { useState, useEffect, useRef } from 'react';

export default function LogStream({ logs, thoughtSignatures, currentAgent, agentColors }) {
  const [activeTab, setActiveTab] = useState('logs'); // logs | thoughts
  const [filter, setFilter] = useState('all'); // all | info | warn | error
  const logsEndRef = useRef(null);
  const thoughtsEndRef = useRef(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (activeTab === 'logs' && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, activeTab]);

  useEffect(() => {
    if (activeTab === 'thoughts' && thoughtsEndRef.current) {
      thoughtsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [thoughtSignatures, activeTab]);

  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter(log => log.level === filter);

  const getLogIcon = (level) => {
    switch (level) {
      case 'error': return '❌';
      case 'warn': return '⚠️';
      case 'success': return '✅';
      default: return 'ℹ️';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  return (
    <div className="log-stream">
      <div className="log-tabs">
        <button
          className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <span className="tab-icon">📋</span>
          Logs
          {logs.length > 0 && (
            <span className="tab-badge">{logs.length}</span>
          )}
        </button>
        <button
          className={`tab-btn ${activeTab === 'thoughts' ? 'active' : ''}`}
          onClick={() => setActiveTab('thoughts')}
        >
          <span className="tab-icon">🧠</span>
          Thought Signatures
          {thoughtSignatures.length > 0 && (
            <span className="tab-badge thought">{thoughtSignatures.length}</span>
          )}
        </button>
      </div>

      {activeTab === 'logs' && (
        <>
          <div className="log-filters">
            {['all', 'info', 'warn', 'error'].map(f => (
              <button
                key={f}
                className={`filter-btn ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          <div className="log-content">
            {filteredLogs.length === 0 ? (
              <div className="empty-logs">
                <span className="empty-icon">📭</span>
                <p>No logs yet</p>
                <p className="empty-hint">Logs will appear here during migration</p>
              </div>
            ) : (
              <div className="log-entries">
                {filteredLogs.map((log, index) => (
                  <div key={index} className={`log-entry level-${log.level}`}>
                    <span className="log-time">{formatTimestamp(log.timestamp)}</span>
                    <span className="log-icon">{getLogIcon(log.level)}</span>
                    <span className="log-message">{log.message}</span>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'thoughts' && (
        <div className="thoughts-content">
          {thoughtSignatures.length === 0 ? (
            <div className="empty-thoughts">
              <span className="empty-icon">💭</span>
              <p>No thought signatures yet</p>
              <p className="empty-hint">Agent reasoning will appear here</p>
            </div>
          ) : (
            <div className="thought-entries">
              {thoughtSignatures.map((thought, index) => (
                <div 
                  key={index} 
                  className="thought-entry"
                  style={{ '--agent-color': agentColors[currentAgent] || '#60a5fa' }}
                >
                  <div className="thought-header">
                    <span className="thought-icon">🧠</span>
                    <span className="thought-time">{formatTimestamp(thought.timestamp)}</span>
                  </div>
                  <div className="thought-content">
                    <p>{thought.content}</p>
                  </div>
                  <div className="thought-connector" />
                </div>
              ))}
              <div ref={thoughtsEndRef} />
            </div>
          )}
        </div>
      )}

      {currentAgent && (
        <div 
          className="current-agent-indicator"
          style={{ '--agent-color': agentColors[currentAgent] }}
        >
          <span className="agent-pulse" />
          <span className="agent-name">{currentAgent} agent active</span>
        </div>
      )}
    </div>
  );
}

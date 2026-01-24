import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import FileTree from './components/FileTree';
import ProgressView from './components/ProgressView';
import DiffViewer from './components/DiffViewer';
import LogStream from './components/LogStream';
import useWebSocket from './hooks/useWebSocket';

export default function App() {
  const [migrationState, setMigrationState] = useState({
    status: 'idle', // idle | running | paused | complete | error
    currentAgent: null,
    currentComponent: null,
    progress: 0,
    components: [],
    logs: [],
    thoughtSignatures: [],
  });

  const [selectedComponent, setSelectedComponent] = useState(null);
  const [repoUrl, setRepoUrl] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const { isConnected, lastMessage, sendMessage } = useWebSocket('ws://localhost:8000/ws');

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const data = lastMessage;

    switch (data.type) {
      case 'agent_status':
        setMigrationState(prev => ({
          ...prev,
          currentAgent: data.agent,
          status: data.status === 'running' ? 'running' : prev.status,
          currentComponent: data.component,
          progress: data.progress || prev.progress,
        }));
        break;

      case 'migration_complete':
        setMigrationState(prev => ({
          ...prev,
          components: prev.components.map(c =>
            c.name === data.component
              ? { ...c, status: data.success ? 'complete' : 'failed', testsPassed: data.tests_passed, testsFailed: data.tests_failed }
              : c
          ),
        }));
        break;

      case 'thought_signature':
        setMigrationState(prev => ({
          ...prev,
          thoughtSignatures: [...prev.thoughtSignatures, { content: data.content, timestamp: data.timestamp }],
        }));
        break;

      case 'log':
        setMigrationState(prev => ({
          ...prev,
          logs: [...prev.logs, { level: data.level, message: data.message, timestamp: new Date().toISOString() }],
        }));
        break;

      case 'components_discovered':
        setMigrationState(prev => ({
          ...prev,
          components: data.components.map(name => ({ name, status: 'pending' })),
        }));
        break;

      case 'error':
        setMigrationState(prev => ({
          ...prev,
          status: 'error',
          logs: [...prev.logs, { level: 'error', message: data.message, timestamp: new Date().toISOString() }],
        }));
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, [lastMessage]);

  const handleStartMigration = async () => {
    if (!repoUrl.trim()) return;
    
    setIsStarting(true);
    try {
      const response = await fetch('http://localhost:8000/api/migrate/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      
      if (response.ok) {
        setMigrationState(prev => ({ ...prev, status: 'running', logs: [], components: [], thoughtSignatures: [] }));
      }
    } catch (error) {
      console.error('Failed to start migration:', error);
    } finally {
      setIsStarting(false);
    }
  };

  const handlePauseMigration = async () => {
    try {
      await fetch('http://localhost:8000/api/migrate/pause', { method: 'POST' });
      setMigrationState(prev => ({ ...prev, status: 'paused' }));
    } catch (error) {
      console.error('Failed to pause migration:', error);
    }
  };

  const agentColors = {
    ingest: '#22d3ee',
    analyze: '#a78bfa',
    plan: '#fbbf24',
    execute: '#34d399',
    test: '#f472b6',
    verify: '#fb923c',
    review: '#60a5fa',
    document: '#94a3b8',
  };

  return (
    <div className="app-container">
      {/* Animated background gradient */}
      <div className="bg-gradient" />
      <div className="bg-noise" />

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <svg viewBox="0 0 32 32" className="logo-icon">
              <path d="M16 2L4 8v16l12 6 12-6V8L16 2z" fill="none" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M16 10v12M10 13v6M22 13v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="16" cy="8" r="2" fill="currentColor"/>
            </svg>
            <span className="logo-text">CodeArchaeologist</span>
          </div>
          <span className="logo-tagline">Autonomous Migration Agent</span>
        </div>

        <div className="header-center">
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot" />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        <div className="header-right">
          {migrationState.status === 'idle' && (
            <div className="start-form">
              <input
                type="text"
                placeholder="https://github.com/user/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="repo-input"
              />
              <button
                onClick={handleStartMigration}
                disabled={isStarting || !repoUrl.trim()}
                className="btn-primary"
              >
                {isStarting ? 'Starting...' : 'Start Migration'}
              </button>
            </div>
          )}
          {migrationState.status === 'running' && (
            <button onClick={handlePauseMigration} className="btn-secondary">
              Pause
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-grid">
        {/* Left Panel - File Tree */}
        <section className="panel panel-files">
          <h2 className="panel-title">
            <span className="panel-icon">📁</span>
            Components
          </h2>
          <FileTree
            components={migrationState.components}
            currentComponent={migrationState.currentComponent}
            onSelect={setSelectedComponent}
            selectedComponent={selectedComponent}
          />
        </section>

        {/* Center Panel - Progress & Diff */}
        <section className="panel panel-main">
          <div className="main-top">
            <ProgressView
              status={migrationState.status}
              currentAgent={migrationState.currentAgent}
              progress={migrationState.progress}
              components={migrationState.components}
              agentColors={agentColors}
            />
          </div>
          <div className="main-bottom">
            <DiffViewer
              component={selectedComponent}
              currentComponent={migrationState.currentComponent}
            />
          </div>
        </section>

        {/* Right Panel - Logs & Thoughts */}
        <section className="panel panel-logs">
          <LogStream
            logs={migrationState.logs}
            thoughtSignatures={migrationState.thoughtSignatures}
            currentAgent={migrationState.currentAgent}
            agentColors={agentColors}
          />
        </section>
      </main>

      {/* Agent Pipeline Visualization */}
      <footer className="agent-pipeline">
        {Object.entries(agentColors).map(([agent, color], index) => {
          const isActive = migrationState.currentAgent === agent;
          const isPast = Object.keys(agentColors).indexOf(migrationState.currentAgent) > index;
          
          return (
            <React.Fragment key={agent}>
              <div
                className={`pipeline-node ${isActive ? 'active' : ''} ${isPast ? 'complete' : ''}`}
                style={{ '--agent-color': color }}
              >
                <div className="node-glow" />
                <span className="node-label">{agent}</span>
              </div>
              {index < Object.keys(agentColors).length - 1 && (
                <div className={`pipeline-connector ${isPast ? 'complete' : ''}`} />
              )}
            </React.Fragment>
          );
        })}
      </footer>
    </div>
  );
}

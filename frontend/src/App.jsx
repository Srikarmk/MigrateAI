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
  const [currentMigrationId, setCurrentMigrationId] = useState(null);
  const [error, setError] = useState(null);
  const [migrationHistory, setMigrationHistory] = useState([]);

  const { isConnected, lastMessage, sendMessage } = useWebSocket('ws://localhost:8000/ws');

  // Fetch migration history on mount and when migrations complete
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/debug/migrations');
        if (response.ok) {
          const data = await response.json();
          if (data.migrations && Array.isArray(data.migrations)) {
            // Filter out current migration and only show completed/failed ones
            const filtered = data.migrations
              .filter(m => {
                const id = m.migration_id || m.id;
                // Exclude current migration
                if (id === currentMigrationId) return false;
                // Only show completed or failed migrations in history
                const status = m.status?.toLowerCase();
                return status === 'completed' || status === 'failed' || status === 'stopped';
              })
              .map(m => ({
                id: m.migration_id || m.id,
                repo_url: m.repo_url,
                status: m.status,
                components_count: m.detected_components?.length || 0,
                created_at: m.created_at,
                updated_at: m.updated_at
              }))
              // Sort by most recent first
              .sort((a, b) => {
                const aTime = new Date(a.updated_at || a.created_at || 0).getTime();
                const bTime = new Date(b.updated_at || b.created_at || 0).getTime();
                return bTime - aTime;
              });
            
            setMigrationHistory(filtered);
          }
        }
      } catch (error) {
        console.error('Failed to fetch migration history:', error);
      }
    };
    
    fetchHistory();
    // Refresh history when migration completes
    if (migrationState.status === 'complete' || migrationState.status === 'failed') {
      const interval = setInterval(fetchHistory, 2000);
      return () => clearInterval(interval);
    }
  }, [migrationState.status, currentMigrationId]);

  // Poll migration status as fallback if WebSocket fails or for progress updates
  useEffect(() => {
    // Poll even if status is 'complete' to catch component status updates
    // Only stop polling if we don't have a migration ID or status is idle
    if (!currentMigrationId || migrationState.status === 'idle') {
      return;
    }

    // Poll less frequently if WebSocket is connected (just as backup)
    // Poll more frequently if WebSocket is disconnected
    // Poll more frequently if status is complete (to catch component updates)
    const pollInterval = (isConnected && migrationState.status !== 'complete') ? 5000 : 2000;

    const pollStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/migrate/${currentMigrationId}`);
        if (response.ok) {
          const data = await response.json();
          
          // Always update progress from polling - this ensures progress bar moves
          const newProgress = data.progress !== undefined && data.progress !== null 
            ? Math.max(0, Math.min(1, data.progress)) 
            : migrationState.progress;
          
          // Always update progress to trigger re-render
          setMigrationState(prev => {
            // Normalize status
            let newStatus = data.status;
            if (newStatus === 'completed') {
              newStatus = 'complete';
            } else if (newStatus === 'failed') {
              newStatus = 'failed';
            } else if (!newStatus) {
              newStatus = prev.status;
            }
            
            // If status is failed, also set error if available
            if (newStatus === 'failed' && data.error && !prev.logs.some(log => log.message.includes(data.error))) {
              // Add error to logs if not already present
              return {
                ...prev,
                status: newStatus,
                progress: newProgress,
                logs: [...prev.logs, {
                  level: 'error',
                  message: data.error,
                  timestamp: new Date().toISOString()
                }]
              };
            }
            
            // Only update if there's a change to avoid unnecessary re-renders
            if (newProgress !== prev.progress || newStatus !== prev.status) {
              console.log('[POLLING] Status update:', prev.status, '→', newStatus, 'Progress:', prev.progress, '→', newProgress);
              return {
                ...prev,
                status: newStatus,
                progress: newProgress
              };
            }
            return prev;
          });
          
          // Update components if they exist
          if (data.detected_components && Array.isArray(data.detected_components) && data.detected_components.length > 0) {
            setMigrationState(prev => {
              const componentNames = data.detected_components.map((c) => {
                if (typeof c === 'string') return c;
                return c.file_path || c.component_name || c;
              }).map(name => String(name).replace(/\\/g, '/'));
              
              // If we don't have components yet, add them
              if (prev.components.length === 0) {
                return {
                  ...prev,
                  components: componentNames.map((name) => ({ name, status: 'pending' }))
                };
              }
              
              // If migration is complete and we have components, mark them all as complete
              // This is a workaround for when WebSocket fails to deliver migration_complete messages
              if (data.status === 'completed' && prev.components.length > 0) {
                const updatedComponents = prev.components.map(c => {
                  // Match by name (normalized)
                  const normalizePath = (path) => String(path).replace(/\\/g, '/').toLowerCase().trim();
                  const cName = normalizePath(c.name);
                  const isInDetected = componentNames.some(name => normalizePath(name) === cName);
                  
                  if (isInDetected && c.status === 'pending') {
                    console.log('[POLLING] Marking component as complete (migration finished):', c.name);
                    return { ...c, status: 'complete' };
                  }
                  return c;
                });
                
                // Check if we need to update
                const hasChanges = updatedComponents.some((c, idx) => c.status !== prev.components[idx].status);
                if (hasChanges) {
                  return {
                    ...prev,
                    components: updatedComponents
                  };
                }
              }
              
              return prev;
            });
          }
        }
      } catch (error) {
        // Only log errors, don't spam console
        if (error.name !== 'AbortError') {
          console.error('Failed to poll migration status:', error);
        }
      }
    };

    // Initial poll
    pollStatus();

    // Set up interval
    const intervalId = setInterval(pollStatus, pollInterval);

    return () => clearInterval(intervalId);
  }, [currentMigrationId, migrationState.status, isConnected]); // Removed components.length from deps

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const data = lastMessage;

    // Handle migration status updates from backend (but don't override agent_status)
    // This is a fallback for messages without explicit type
    if (data.status && data.type !== 'agent_status' && data.type !== 'migration_status') {
      const newProgress = data.progress !== undefined && data.progress !== null 
        ? Math.max(0, Math.min(1, data.progress)) 
        : migrationState.progress;
      let newStatus = data.status;
      if (newStatus === 'completed') {
        newStatus = 'complete';
      }
      setMigrationState(prev => ({
        ...prev,
        status: newStatus,
        progress: newProgress,
      }));
    }

    switch (data.type) {
      case 'agent_status':
        setMigrationState(prev => {
          // Only update status if it's a meaningful change
          let newStatus = prev.status;
          if (data.status === 'running') {
            newStatus = 'running';
          } else if (data.status === 'paused') {
            newStatus = 'paused';
          } else if (data.status === 'stopped') {
            newStatus = 'stopped';
          } else if (data.status === 'completed' || data.status === 'complete') {
            // Don't set to complete here - wait for final migration_status
            // Keep as running until final completion
            if (prev.status !== 'complete') {
              newStatus = 'running';
            }
          }
          
          // Update currentAgent - always update when agent changes
          let updatedAgent = prev.currentAgent;
          if (data.agent !== undefined && data.agent !== null) {
            updatedAgent = data.agent;
          }
          // Don't clear agent on completion - keep it for visual feedback
          
          // Update component status if component is being processed
          let updatedComponents = prev.components;
          if (data.component && data.status === 'running') {
            updatedComponents = prev.components.map(c => {
              // Match by component name (could be full path or just name)
              const matches = c.name === data.component || 
                            c.name.endsWith(data.component) || 
                            data.component.endsWith(c.name);
              return matches ? { ...c, status: 'in_progress' } : c;
            });
          }
          
          // Always update progress from agent_status - this ensures progress bar moves
          const newProgress = data.progress !== undefined && data.progress !== null 
            ? Math.max(0, Math.min(1, data.progress)) 
            : prev.progress;
          
          return {
            ...prev,
            currentAgent: updatedAgent,
            status: newStatus,
            currentComponent: data.component || prev.currentComponent,
            progress: newProgress,
            components: updatedComponents,
          };
        });
        break;

      case 'migration_complete':
        setMigrationState(prev => {
          console.log('[MIGRATION_COMPLETE] Received for:', data.component);
          console.log('[MIGRATION_COMPLETE] Current components count:', prev.components.length);
          console.log('[MIGRATION_COMPLETE] Current components:', prev.components.map(c => ({ name: c.name, status: c.status })));
          
          // If no components yet, we can't match - this shouldn't happen but handle it
          if (prev.components.length === 0) {
            console.warn('[MIGRATION_COMPLETE] ⚠️ No components in state yet! Adding component directly.');
            return {
              ...prev,
              components: [{ name: data.component, status: data.success ? 'complete' : 'failed', testsPassed: data.tests_passed, testsFailed: data.tests_failed }]
            };
          }
          
          const normalizePath = (path) => {
            if (!path) return '';
            return String(path).replace(/\\/g, '/').toLowerCase().trim();
          };
          
          const targetName = normalizePath(data.component);
          console.log('[MIGRATION_COMPLETE] Normalized target:', targetName);
          
          let foundMatch = false;
          const updatedComponents = prev.components.map(c => {
            const cName = normalizePath(c.name);
            console.log('[MIGRATION_COMPLETE] Comparing:', cName, 'with', targetName);
            
            // Try multiple matching strategies
            const exactMatch = cName === targetName;
            const endsWithMatch = cName.endsWith(targetName) || targetName.endsWith(cName);
            const containsMatch = cName.includes(targetName) || targetName.includes(cName);
            // Also try matching just the filename
            const cFileName = cName.split('/').pop();
            const targetFileName = targetName.split('/').pop();
            const fileNameMatch = cFileName && targetFileName && cFileName === targetFileName;
            
            const matches = exactMatch || endsWithMatch || containsMatch || fileNameMatch;
            
            if (matches) {
              foundMatch = true;
              console.log('[MIGRATION_COMPLETE] ✅ Matched:', c.name, 'with', data.component);
              console.log('[MIGRATION_COMPLETE] Match type:', exactMatch ? 'exact' : endsWithMatch ? 'endsWith' : containsMatch ? 'contains' : 'filename');
              return { 
                ...c, 
                status: data.success ? 'complete' : 'failed', 
                testsPassed: data.tests_passed, 
                testsFailed: data.tests_failed 
              };
            }
            return c;
          });
          
          if (!foundMatch) {
            console.error('[MIGRATION_COMPLETE] ❌ NO MATCH FOUND!');
            console.error('[MIGRATION_COMPLETE] Target component:', data.component);
            console.error('[MIGRATION_COMPLETE] Available components:', prev.components.map(c => c.name));
            // Still update to show we tried
            return {
              ...prev,
              components: updatedComponents,
            };
          }
          
          const hasChanges = updatedComponents.some((c, idx) => c.status !== prev.components[idx].status);
          if (hasChanges) {
            console.log('[MIGRATION_COMPLETE] ✅ Updated components:', updatedComponents.map(c => ({ name: c.name, status: c.status })));
          }
          
          return {
            ...prev,
            components: updatedComponents,
          };
        });
        break;

      case 'thought_signature':
        setMigrationState(prev => {
          // Ensure timestamp is a valid ISO string
          let timestamp = data.timestamp;
          if (typeof timestamp === 'number') {
            // If it's a Unix timestamp (seconds), convert to milliseconds
            // Check if it's in seconds (less than year 2000 in ms) or milliseconds
            if (timestamp < 946684800) { // Year 2000 in seconds
              timestamp = new Date(timestamp * 1000).toISOString();
            } else {
              timestamp = new Date(timestamp).toISOString();
            }
          } else if (!timestamp || typeof timestamp !== 'string') {
            timestamp = new Date().toISOString();
          }
          // If it's already an ISO string, use it as is
          console.log('[THOUGHT_SIGNATURE] Received:', data.content, 'timestamp:', timestamp);
          return {
            ...prev,
            thoughtSignatures: [...prev.thoughtSignatures, { content: data.content, timestamp }],
          };
        });
        break;

      case 'log':
        setMigrationState(prev => ({
          ...prev,
          logs: [...prev.logs, { level: data.level, message: data.message, timestamp: new Date().toISOString() }],
        }));
        break;

      case 'components_discovered':
        setMigrationState(prev => {
          console.log('[COMPONENTS] Components discovered:', data.components);
          console.log('[COMPONENTS] Component count:', data.components?.length || 0);
          // Always update with the new list - replace existing
          const updated = (data.components || []).map(name => {
            const normalized = String(name).replace(/\\/g, '/');
            console.log('[COMPONENTS] Adding component:', normalized);
            return { name: normalized, status: 'pending' };
          });
          console.log('[COMPONENTS] Final component list:', updated.map(c => c.name));
          return {
            ...prev,
            components: updated
          };
        });
        break;

      case 'error':
        setMigrationState(prev => ({
          ...prev,
          status: 'failed',
          logs: [...prev.logs, {
            level: 'error',
            message: data.message || 'An error occurred',
            timestamp: new Date().toISOString()
          }]
        }));
        setError(data.message || 'An error occurred');
        break;

      case 'migration_status':
        setMigrationState(prev => {
          // Don't override currentAgent if we have one and status is still running
          let updatedAgent = prev.currentAgent;
          // If status is a specific agent stage, update currentAgent
          const agentStatuses = ['ingesting', 'analyzing', 'planning', 'executing', 'testing', 'verifying', 'reviewing', 'documenting'];
          if (agentStatuses.includes(data.status)) {
            const agentMap = {
              'ingesting': 'ingest',
              'analyzing': 'analyze',
              'planning': 'plan',
              'executing': 'execute',
              'testing': 'test',
              'verifying': 'verify',
              'reviewing': 'review',
              'documenting': 'document'
            };
            updatedAgent = agentMap[data.status];
          }
          
          // Always update progress from migration_status messages
          const newProgress = data.progress !== undefined && data.progress !== null 
            ? Math.max(0, Math.min(1, data.progress)) 
            : prev.progress;
          
          // Normalize status
          let newStatus = data.status;
          if (newStatus === 'completed') {
            newStatus = 'complete';
          } else if (newStatus === 'failed') {
            newStatus = 'failed';
          } else if (!newStatus) {
            newStatus = prev.status;
          }
          
          console.log('[MIGRATION_STATUS] Status:', prev.status, '→', newStatus, 'Progress:', prev.progress, '→', newProgress);
          
          return {
            ...prev,
            status: newStatus,
            progress: newProgress,
            currentAgent: updatedAgent || prev.currentAgent,
          };
        });
        break;

      case 'error':
        setMigrationState(prev => ({
          ...prev,
          status: 'failed',
          logs: [...prev.logs, {
            level: 'error',
            message: data.message || 'An error occurred',
            timestamp: new Date().toISOString()
          }]
        }));
        setError(data.message || 'An error occurred');
        break;

      default:
        // Handle any message with a status field
        if (data.status && !data.type) {
          let newStatus = data.status;
          if (newStatus === 'completed') {
            newStatus = 'complete';
          } else if (newStatus === 'failed') {
            newStatus = 'failed';
          }
          setMigrationState(prev => ({
            ...prev,
            status: newStatus,
          }));
        } else {
          console.log('Unknown message type:', data.type || 'no type', data);
        }
    }
  }, [lastMessage]);

  const handleStartMigration = async () => {
    if (!repoUrl.trim()) {
      alert('Please enter a repository URL or path');
      return;
    }
    
    if (isStarting) return; // Prevent double-click
    
    setIsStarting(true);
    try {
      const response = await fetch('http://localhost:8000/api/migrate/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      });
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch {
          // If response is not JSON, use status text
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      const migrationId = data.migration_id;
      
      if (!migrationId) {
        throw new Error('No migration ID returned from server');
      }
      
      setCurrentMigrationId(migrationId);
      setMigrationState(prev => ({ 
        ...prev, 
        status: 'running', 
        logs: [], 
        components: [], 
        thoughtSignatures: [],
        currentAgent: 'ingest', // Start with ingest agent
        progress: 0,
        currentComponent: null
      }));
      
      // Send migration_id to WebSocket
      if (isConnected) {
        sendMessage({ migration_id: migrationId });
        console.log('Sent migration_id to WebSocket:', migrationId);
      } else {
        // If not connected, try to connect
        console.warn('WebSocket not connected, migration started but real-time updates may not work');
        console.warn('Status polling will be used as fallback');
      }
      
      // Add initial log - but state is already reset above, so just add to empty logs
      setMigrationState(prev => ({
        ...prev,
        logs: [{ 
          level: 'info', 
          message: `Migration started with ID: ${migrationId}`,
          timestamp: new Date().toISOString()
        }]
      }));
    } catch (error) {
      console.error('Failed to start migration:', error);
      const errorMessage = error.message || 'Unknown error occurred';
      setError(errorMessage);
      setMigrationState(prev => ({
        ...prev,
        status: 'failed',
        logs: [{
          level: 'error', 
          message: `Failed to start migration: ${errorMessage}`, 
          timestamp: new Date().toISOString() 
        }]
      }));
      // Clear error after 5 seconds
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsStarting(false);
    }
  };

  const handlePauseMigration = async () => {
    if (!currentMigrationId) {
      console.error('No migration ID available');
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/migrate/pause?migration_id=${currentMigrationId}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMigrationState(prev => ({ ...prev, status: 'paused' }));
        console.log('Migration paused:', data);
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Failed to pause migration:', errorData);
        
        // If migration is already completed/stopped, update frontend status
        if (errorData.current_status) {
          setMigrationState(prev => ({ ...prev, status: errorData.current_status }));
        }
        
        alert(`Failed to pause: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to pause migration:', error);
      alert(`Error pausing migration: ${error.message}`);
    }
  };

  const handleResumeMigration = async () => {
    if (!currentMigrationId) {
      console.error('No migration ID available');
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/migrate/resume?migration_id=${currentMigrationId}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMigrationState(prev => ({ ...prev, status: 'running' }));
        console.log('Migration resumed:', data);
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Failed to resume migration:', errorData);
        alert(`Failed to resume: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to resume migration:', error);
      alert(`Error resuming migration: ${error.message}`);
    }
  };

  const handleStopMigration = async () => {
    if (!currentMigrationId) {
      console.error('No migration ID available');
      return;
    }
    
    if (!confirm('Are you sure you want to stop this migration?')) {
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/migrate/stop?migration_id=${currentMigrationId}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMigrationState(prev => ({ ...prev, status: 'stopped' }));
        console.log('Migration stopped:', data);
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Failed to stop migration:', errorData);
        alert(`Failed to stop: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to stop migration:', error);
      alert(`Error stopping migration: ${error.message}`);
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
          {(migrationState.status === 'idle' || migrationState.status === 'failed' || migrationState.status === 'complete') && (
            <div className="start-form">
              <input
                type="text"
                placeholder="https://github.com/user/repo or ./demo_codebase"
                value={repoUrl}
                onChange={(e) => {
                  setRepoUrl(e.target.value);
                  setError(null); // Clear error when user types
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !isStarting && repoUrl.trim()) {
                    handleStartMigration();
                  }
                }}
                className="repo-input"
                disabled={isStarting}
                style={{ borderColor: error ? '#ef4444' : undefined }}
              />
              {error && (
                <div style={{ 
                  color: '#ef4444', 
                  fontSize: '12px', 
                  marginTop: '4px',
                  marginBottom: '4px'
                }}>
                  {error}
                </div>
              )}
              <button
                onClick={handleStartMigration}
                disabled={isStarting || !repoUrl.trim()}
                className="btn-primary"
                style={{ 
                  opacity: (isStarting || !repoUrl.trim()) ? 0.6 : 1, 
                  cursor: (isStarting || !repoUrl.trim()) ? 'not-allowed' : 'pointer',
                  pointerEvents: (isStarting || !repoUrl.trim()) ? 'none' : 'auto'
                }}
              >
                {isStarting ? 'Starting...' : 'Start Migration'}
              </button>
            </div>
          )}
          
          {(migrationState.status === 'complete' || migrationState.status === 'failed' || migrationState.status === 'stopped') && (
            <button
              onClick={() => {
                // Complete reset for new migration
                setMigrationState({
                  status: 'idle',
                  currentAgent: null,
                  currentComponent: null,
                  progress: 0,
                  components: [],
                  logs: [],
                  thoughtSignatures: [],
                });
                setCurrentMigrationId(null);
                setRepoUrl('');
                setSelectedComponent(null);
                setError(null);
                setIsStarting(false);
                // Refresh history to show the completed migration
                setTimeout(() => {
                  fetch('http://localhost:8000/api/debug/migrations')
                    .then(r => r.json())
                    .then(data => {
                      if (data.migrations && Array.isArray(data.migrations)) {
                        const filtered = data.migrations
                          .filter(m => {
                            const status = m.status?.toLowerCase();
                            return status === 'completed' || status === 'failed' || status === 'stopped';
                          })
                          .map(m => ({
                            id: m.migration_id || m.id,
                            repo_url: m.repo_url,
                            status: m.status,
                            components_count: m.detected_components?.length || 0,
                            created_at: m.created_at,
                            updated_at: m.updated_at
                          }))
                          .sort((a, b) => {
                            const aTime = new Date(a.updated_at || a.created_at || 0).getTime();
                            const bTime = new Date(b.updated_at || b.created_at || 0).getTime();
                            return bTime - aTime;
                          });
                        setMigrationHistory(filtered);
                      }
                    })
                    .catch(err => console.error('Failed to refresh history:', err));
                }, 500);
              }}
              className="btn-primary"
            >
              🚀 Start New Migration
            </button>
          )}
          {migrationState.status === 'running' && (
            <>
              <button onClick={handlePauseMigration} className="btn-secondary">
                Pause
              </button>
              <button onClick={handleStopMigration} className="btn-danger" style={{ marginLeft: '10px', backgroundColor: '#ef4444' }}>
                Stop
              </button>
            </>
          )}
          {migrationState.status === 'paused' && (
            <>
              <button onClick={handleResumeMigration} className="btn-primary">
                Resume
              </button>
              <button onClick={handleStopMigration} className="btn-danger" style={{ marginLeft: '10px', backgroundColor: '#ef4444' }}>
                Stop
              </button>
            </>
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

        {/* Right Panel - Logs, Thoughts & History */}
        <section className="panel panel-logs">
          <div className="logs-container">
            <LogStream
              logs={migrationState.logs}
              thoughtSignatures={migrationState.thoughtSignatures}
              currentAgent={migrationState.currentAgent}
              agentColors={agentColors}
            />
          </div>
          <div className="history-container">
            <div className="history-header">
              <h3>Migration History</h3>
            </div>
            <div className="history-list-compact">
              {migrationHistory.length === 0 ? (
                <div className="history-empty">
                  <p>No previous migrations</p>
                </div>
              ) : (
                migrationHistory.slice(0, 5).map((migration, idx) => (
                  <div key={migration.id || idx} className="history-item-compact">
                    <div className="history-item-header">
                      <span className="history-repo-compact">{migration.repo_url?.split('/').pop() || migration.repo_url || 'Unknown'}</span>
                      <span className={`history-status status-${migration.status}`}>
                        {migration.status === 'completed' ? '✓' : migration.status === 'failed' ? '✗' : '○'}
                      </span>
                    </div>
                    <div className="history-item-meta-compact">
                      <span>{migration.components_count || 0} comps</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </main>

      {/* Footer - Just New Migration Button when complete */}
      {migrationState.status === 'complete' && (
        <footer className="migration-footer-simple">
          <button 
            className="btn-new-migration-footer"
            onClick={() => {
              setMigrationState({
                status: 'idle',
                currentAgent: null,
                currentComponent: null,
                progress: 0,
                components: [],
                logs: [],
                thoughtSignatures: [],
              });
              setCurrentMigrationId(null);
              setRepoUrl('');
              setSelectedComponent(null);
              setError(null);
            }}
          >
            🚀 Start New Migration
          </button>
        </footer>
      )}
    </div>
  );
}

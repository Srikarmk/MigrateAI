import React, { useState, useEffect } from 'react';

export default function DiffViewer({ component, currentComponent }) {
  const [diffData, setDiffData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState('split'); // split | unified

  const displayComponent = component || currentComponent;

  useEffect(() => {
    if (!displayComponent) {
      setDiffData(null);
      return;
    }

    const fetchDiff = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/diff/${encodeURIComponent(displayComponent)}`);
        if (response.ok) {
          const data = await response.json();
          setDiffData(data);
        }
      } catch (error) {
        console.error('Failed to fetch diff:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDiff();
  }, [displayComponent]);

  const highlightSyntax = (code, type = 'jsx') => {
    // Simple syntax highlighting
    return code
      .replace(/(import|export|from|const|let|var|function|return|if|else|class|extends)/g, '<span class="keyword">$1</span>')
      .replace(/(['"`].*?['"`])/g, '<span class="string">$1</span>')
      .replace(/(\{|\}|\(|\)|\[|\])/g, '<span class="bracket">$1</span>')
      .replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
      .replace(/(&lt;[A-Z][a-zA-Z]*)/g, '<span class="component">$1</span>')
      .replace(/(useState|useEffect|useCallback|useMemo|useRef|useContext)/g, '<span class="hook">$1</span>');
  };

  if (!displayComponent) {
    return (
      <div className="diff-viewer empty">
        <div className="empty-state-prominent">
          <div className="empty-icon-large">📋</div>
          <h2 className="empty-title">Migration Complete!</h2>
          <p className="empty-message">Select a component from the left panel to view the migration changes</p>
          <div className="empty-instructions">
            <div className="instruction-step">
              <span className="step-number">1</span>
              <span>Click on any component in the left panel</span>
            </div>
            <div className="instruction-step">
              <span className="step-number">2</span>
              <span>View the before/after code comparison</span>
            </div>
            <div className="instruction-step">
              <span className="step-number">3</span>
              <span>See how class components were converted to hooks</span>
            </div>
          </div>
          <div className="empty-arrow">←</div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="diff-viewer loading">
        <div className="loading-spinner" />
        <p>Loading diff...</p>
      </div>
    );
  }

  // Demo data for when backend isn't connected
  const demoData = {
    before: `class ${displayComponent.replace('.jsx', '')} extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0, loading: false };
  }

  componentDidMount() {
    this.fetchData();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.id !== this.props.id) {
      this.fetchData();
    }
  }

  fetchData = async () => {
    this.setState({ loading: true });
    // fetch logic...
    this.setState({ loading: false });
  }

  render() {
    const { count, loading } = this.state;
    return (
      <div>
        {loading ? 'Loading...' : count}
      </div>
    );
  }
}`,
    after: `function ${displayComponent.replace('.jsx', '')}({ id }) {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    // fetch logic...
    setLoading(false);
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div>
      {loading ? 'Loading...' : count}
    </div>
  );
}`,
  };

  const data = diffData || demoData;

  return (
    <div className="diff-viewer" style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="diff-header">
        <div className="diff-title">
          <span className="diff-icon">🔄</span>
          <span className="diff-filename">{displayComponent}</span>
          {currentComponent === displayComponent && (
            <span className="live-badge">
              <span className="live-dot" />
              Live
            </span>
          )}
        </div>
        <div className="diff-controls">
          <button
            className={`view-mode-btn ${viewMode === 'split' ? 'active' : ''}`}
            onClick={() => setViewMode('split')}
          >
            Split
          </button>
          <button
            className={`view-mode-btn ${viewMode === 'unified' ? 'active' : ''}`}
            onClick={() => setViewMode('unified')}
          >
            Unified
          </button>
        </div>
      </div>

      <div className={`diff-content ${viewMode}`}>
        {viewMode === 'split' ? (
          <>
            <div className="diff-pane before">
              <div className="pane-header">
                <span className="pane-label">Before (Class Component)</span>
                <span className="pane-badge old">Old</span>
              </div>
              <pre className="code-block">
                <code dangerouslySetInnerHTML={{ __html: highlightSyntax(data.before) }} />
              </pre>
            </div>
            <div className="diff-divider">
              <div className="divider-arrow">→</div>
            </div>
            <div className="diff-pane after">
              <div className="pane-header">
                <span className="pane-label">After (Hooks)</span>
                <span className="pane-badge new">New</span>
              </div>
              <pre className="code-block">
                <code dangerouslySetInnerHTML={{ __html: highlightSyntax(data.after) }} />
              </pre>
            </div>
          </>
        ) : (
          <div className="diff-pane unified">
            <div className="pane-header">
              <span className="pane-label">Unified Diff</span>
            </div>
            <pre className="code-block unified-diff">
              {data.before.split('\n').map((line, i) => (
                <div key={`old-${i}`} className="diff-line removed">
                  <span className="line-marker">-</span>
                  <code dangerouslySetInnerHTML={{ __html: highlightSyntax(line) }} />
                </div>
              ))}
              <div className="diff-separator">───────────────────</div>
              {data.after.split('\n').map((line, i) => (
                <div key={`new-${i}`} className="diff-line added">
                  <span className="line-marker">+</span>
                  <code dangerouslySetInnerHTML={{ __html: highlightSyntax(line) }} />
                </div>
              ))}
            </pre>
          </div>
        )}
      </div>

      <div className="diff-footer">
        <div className="diff-stats">
          <span className="stat additions">+{data.after.split('\n').length} lines</span>
          <span className="stat deletions">-{data.before.split('\n').length} lines</span>
        </div>
      </div>
    </div>
  );
}

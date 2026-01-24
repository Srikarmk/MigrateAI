import React from 'react';

export default function FileTree({ components, currentComponent, onSelect, selectedComponent }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return <span className="status-icon complete">✓</span>;
      case 'failed':
        return <span className="status-icon failed">✗</span>;
      case 'running':
        return <span className="status-icon running">●</span>;
      default:
        return <span className="status-icon pending">○</span>;
    }
  };

  const getFileIcon = (filename) => {
    if (filename.endsWith('.jsx') || filename.endsWith('.tsx')) {
      return '⚛️';
    }
    if (filename.endsWith('.js') || filename.endsWith('.ts')) {
      return '📜';
    }
    if (filename.endsWith('.css') || filename.endsWith('.scss')) {
      return '🎨';
    }
    return '📄';
  };

  if (components.length === 0) {
    return (
      <div className="file-tree-empty">
        <div className="empty-icon">🔍</div>
        <p>No components discovered yet</p>
        <p className="empty-hint">Start a migration to analyze the codebase</p>
      </div>
    );
  }

  return (
    <div className="file-tree">
      <div className="tree-header">
        <span className="tree-count">{components.length} components</span>
      </div>
      <ul className="tree-list">
        {components.map((component) => {
          const isActive = currentComponent === component.name;
          const isSelected = selectedComponent === component.name;
          
          return (
            <li
              key={component.name}
              className={`tree-item ${isActive ? 'active' : ''} ${isSelected ? 'selected' : ''} status-${component.status}`}
              onClick={() => onSelect(component.name)}
            >
              <span className="item-icon">{getFileIcon(component.name)}</span>
              <span className="item-name">{component.name}</span>
              {getStatusIcon(component.status)}
              {isActive && (
                <span className="active-indicator">
                  <span className="pulse-ring" />
                </span>
              )}
            </li>
          );
        })}
      </ul>
      
      <div className="tree-legend">
        <div className="legend-item">
          <span className="status-icon complete">✓</span>
          <span>Migrated</span>
        </div>
        <div className="legend-item">
          <span className="status-icon running">●</span>
          <span>In Progress</span>
        </div>
        <div className="legend-item">
          <span className="status-icon pending">○</span>
          <span>Pending</span>
        </div>
        <div className="legend-item">
          <span className="status-icon failed">✗</span>
          <span>Failed</span>
        </div>
      </div>
    </div>
  );
}

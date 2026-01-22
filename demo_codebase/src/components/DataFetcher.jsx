import React, { Component } from 'react';

/**
 * DataFetcher component - Class component with API calls
 * Uses: componentDidMount, componentDidUpdate, async/await, error handling, this.state
 */
class DataFetcher extends Component {
  constructor(props) {
    super(props);
    this.state = {
      data: null,
      loading: true,
      error: null,
      fetchCount: 0
    };
  }

  componentDidMount() {
    this.fetchData();
  }

  componentDidUpdate(prevProps) {
    // Refetch data when URL prop changes
    if (prevProps.url !== this.props.url) {
      this.fetchData();
    }
  }

  fetchData = async () => {
    this.setState({ loading: true, error: null });

    try {
      // Simulate API call with delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock API response
      const mockData = {
        id: Math.floor(Math.random() * 1000),
        title: 'Sample Data',
        description: 'This is mock data fetched from the API',
        timestamp: new Date().toISOString(),
        items: [
          { id: 1, name: 'Item 1', value: 100 },
          { id: 2, name: 'Item 2', value: 200 },
          { id: 3, name: 'Item 3', value: 300 }
        ]
      };

      this.setState(prevState => ({
        data: mockData,
        loading: false,
        fetchCount: prevState.fetchCount + 1
      }));
    } catch (error) {
      this.setState({
        error: error.message || 'Failed to fetch data',
        loading: false
      });
    }
  }

  handleRefresh = () => {
    this.fetchData();
  }

  render() {
    const { data, loading, error, fetchCount } = this.state;

    if (loading) {
      return (
        <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
          <h2>Data Fetcher</h2>
          <p>Loading data from {this.props.url}...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
          <h2>Data Fetcher</h2>
          <p style={{ color: 'red' }}>Error: {error}</p>
          <button onClick={this.handleRefresh}>Retry</button>
        </div>
      );
    }

    return (
      <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
        <h2>Data Fetcher</h2>
        <p><strong>URL:</strong> {this.props.url}</p>
        <p><strong>Fetch Count:</strong> {fetchCount}</p>
        <button onClick={this.handleRefresh} style={{ marginBottom: '10px' }}>
          Refresh Data
        </button>
        {data && (
          <div style={{ textAlign: 'left', marginTop: '10px' }}>
            <h3>{data.title}</h3>
            <p>{data.description}</p>
            <p><strong>ID:</strong> {data.id}</p>
            <p><strong>Timestamp:</strong> {data.timestamp}</p>
            <h4>Items:</h4>
            <ul>
              {data.items.map(item => (
                <li key={item.id}>
                  {item.name}: {item.value}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }
}

export default DataFetcher;

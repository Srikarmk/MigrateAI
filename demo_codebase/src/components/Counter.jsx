import React, { Component } from 'react';

/**
 * Counter component - Simple class component with state
 * Uses: constructor, this.state, this.setState
 */
class Counter extends Component {
  constructor(props) {
    super(props);
    this.state = {
      count: 0
    };
  }

  increment = () => {
    this.setState({ count: this.state.count + 1 });
  }

  decrement = () => {
    this.setState({ count: this.state.count - 1 });
  }

  reset = () => {
    this.setState({ count: 0 });
  }

  render() {
    return (
      <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
        <h2>Counter</h2>
        <p>Count: {this.state.count}</p>
        <button onClick={this.increment}>Increment</button>
        <button onClick={this.decrement}>Decrement</button>
        <button onClick={this.reset}>Reset</button>
      </div>
    );
  }
}

export default Counter;

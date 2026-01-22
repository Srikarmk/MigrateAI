import React, { Component } from 'react';

/**
 * Timer component - Class component with cleanup
 * Uses: componentDidMount, componentWillUnmount, setInterval, this.state
 */
class Timer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      seconds: 0,
      isRunning: false
    };
    this.timerId = null;
  }

  componentDidMount() {
    // Auto-start timer on mount
    this.startTimer();
  }

  componentWillUnmount() {
    // Cleanup: clear interval when component unmounts
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }

  startTimer = () => {
    if (!this.state.isRunning) {
      this.setState({ isRunning: true });
      this.timerId = setInterval(() => {
        this.setState(prevState => ({
          seconds: prevState.seconds + 1
        }));
      }, 1000);
    }
  }

  stopTimer = () => {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
      this.setState({ isRunning: false });
    }
  }

  resetTimer = () => {
    this.stopTimer();
    this.setState({ seconds: 0 });
  }

  formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  render() {
    return (
      <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
        <h2>Timer</h2>
        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
          {this.formatTime(this.state.seconds)}
        </p>
        <button onClick={this.startTimer} disabled={this.state.isRunning}>
          Start
        </button>
        <button onClick={this.stopTimer} disabled={!this.state.isRunning}>
          Stop
        </button>
        <button onClick={this.resetTimer}>Reset</button>
      </div>
    );
  }
}

export default Timer;

import React, { Component } from 'react';

/**
 * UserProfile component - Class component with lifecycle methods
 * Uses: componentDidMount, componentDidUpdate, this.state, this.setState
 */
class UserProfile extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: null,
      loading: true,
      error: null,
      previousUserId: null
    };
  }

  componentDidMount() {
    // Fetch user data when component mounts
    this.fetchUser(this.props.userId);
  }

  componentDidUpdate(prevProps) {
    // Fetch new user data when userId prop changes
    if (prevProps.userId !== this.props.userId) {
      this.fetchUser(this.props.userId);
    }
  }

  fetchUser = async (userId) => {
    this.setState({ loading: true, error: null });
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock user data
      const user = {
        id: userId,
        name: `User ${userId}`,
        email: `user${userId}@example.com`,
        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${userId}`
      };
      
      this.setState({
        user,
        loading: false,
        previousUserId: userId
      });
    } catch (error) {
      this.setState({
        error: error.message,
        loading: false
      });
    }
  }

  render() {
    const { user, loading, error } = this.state;

    if (loading) {
      return <div>Loading user profile...</div>;
    }

    if (error) {
      return <div>Error: {error}</div>;
    }

    if (!user) {
      return <div>No user found</div>;
    }

    return (
      <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
        <h2>User Profile</h2>
        <img src={user.avatar} alt={user.name} style={{ width: '100px', height: '100px' }} />
        <p><strong>Name:</strong> {user.name}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>ID:</strong> {user.id}</p>
      </div>
    );
  }
}

export default UserProfile;

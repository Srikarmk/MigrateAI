import React, { Component } from 'react';

/**
 * ContactForm component - Class component with form handling
 * Uses: constructor, this.state, this.setState, form events, refs
 */
class ContactForm extends Component {
  constructor(props) {
    super(props);
    this.state = {
      name: '',
      email: '',
      message: '',
      submitted: false,
      errors: {}
    };
    this.nameInputRef = React.createRef();
  }

  componentDidMount() {
    // Focus on name input when component mounts
    if (this.nameInputRef.current) {
      this.nameInputRef.current.focus();
    }
  }

  handleChange = (e) => {
    const { name, value } = e.target;
    this.setState(prevState => ({
      [name]: value,
      errors: {
        ...prevState.errors,
        [name]: '' // Clear error when user types
      }
    }));
  }

  validate = () => {
    const { name, email, message } = this.state;
    const errors = {};

    if (!name.trim()) {
      errors.name = 'Name is required';
    }

    if (!email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Invalid email format';
    }

    if (!message.trim()) {
      errors.message = 'Message is required';
    }

    return errors;
  }

  handleSubmit = (e) => {
    e.preventDefault();
    const errors = this.validate();

    if (Object.keys(errors).length > 0) {
      this.setState({ errors });
      return;
    }

    // Simulate form submission
    this.setState({ submitted: true });
    
    // Reset form after 2 seconds
    setTimeout(() => {
      this.setState({
        name: '',
        email: '',
        message: '',
        submitted: false,
        errors: {}
      });
    }, 2000);
  }

  render() {
    const { name, email, message, submitted, errors } = this.state;

    if (submitted) {
      return (
        <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
          <h2>Contact Form</h2>
          <p style={{ color: 'green' }}>Thank you! Your message has been submitted.</p>
        </div>
      );
    }

    return (
      <div style={{ margin: '20px', padding: '20px', border: '1px solid #ccc' }}>
        <h2>Contact Form</h2>
        <form onSubmit={this.handleSubmit}>
          <div>
            <label>
              Name:
              <input
                type="text"
                name="name"
                value={name}
                onChange={this.handleChange}
                ref={this.nameInputRef}
                style={{ marginLeft: '10px', padding: '5px' }}
              />
            </label>
            {errors.name && <div style={{ color: 'red' }}>{errors.name}</div>}
          </div>
          <div style={{ marginTop: '10px' }}>
            <label>
              Email:
              <input
                type="email"
                name="email"
                value={email}
                onChange={this.handleChange}
                style={{ marginLeft: '10px', padding: '5px' }}
              />
            </label>
            {errors.email && <div style={{ color: 'red' }}>{errors.email}</div>}
          </div>
          <div style={{ marginTop: '10px' }}>
            <label>
              Message:
              <textarea
                name="message"
                value={message}
                onChange={this.handleChange}
                rows="4"
                style={{ marginLeft: '10px', padding: '5px', width: '300px' }}
              />
            </label>
            {errors.message && <div style={{ color: 'red' }}>{errors.message}</div>}
          </div>
          <button type="submit" style={{ marginTop: '10px', padding: '8px 16px' }}>
            Submit
          </button>
        </form>
      </div>
    );
  }
}

export default ContactForm;

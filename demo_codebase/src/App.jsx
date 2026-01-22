import React from 'react';
import Counter from './components/Counter';
import UserProfile from './components/UserProfile';
import Timer from './components/Timer';
import ContactForm from './components/ContactForm';
import DataFetcher from './components/DataFetcher';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Demo React App - Class Components</h1>
        <Counter />
        <UserProfile userId={1} />
        <Timer />
        <ContactForm />
        <DataFetcher url="https://api.example.com/data" />
      </header>
    </div>
  );
}

export default App;

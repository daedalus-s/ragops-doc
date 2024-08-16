import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('https://77ywt7l8yd.execute-api.us-east-1.amazonaws.com/prod/recommend', { question });
      setAnswer(response.data.answer);
    } catch (error) {
      console.error('Error:', error);
      setAnswer('An error occurred. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>RAGOps Product Recommender</h1>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question about Amazon products"
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : 'Get Answer'}
          </button>
        </form>
        {answer && (
          <div className="answer">
            <h2>Answer:</h2>
            <p>{answer}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
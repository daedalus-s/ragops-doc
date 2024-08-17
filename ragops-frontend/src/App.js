import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await axios.post('https://77ywt7l8yd.execute-api.us-east-1.amazonaws.com/prod/recommend', { question });
      console.log('API Response:', result.data); // Log the response for debugging
      setResponse(result.data);
    } catch (err) {
      setError('An error occurred. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>RAGOps Product Recommender</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter your question"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Get Answer'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {response && (
        <div className="response">
          <h2>Answer:</h2>
          <p>{response.answer || 'No answer provided'}</p>
          
          {response.keywords && response.keywords.length > 0 && (
            <>
              <h3>Keywords:</h3>
              <ul>
                {response.keywords.map((keyword, index) => (
                  <li key={index}>{keyword}</li>
                ))}
              </ul>
            </>
          )}
          
          <p>Number of relevant products found: {response.num_results || 0}</p>
        </div>
      )}
    </div>
  );
}

export default App;
import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_URL}/plans`)
      .then(res => res.json())
      .then(setPlans)
      .catch(console.error);
  }, []);

  return (
    <div className="App">
      <h1>Available Plans</h1>
      <ul>
        {plans.map(p => (
          <li key={p.id}>
            {p.name} — ${p.price_usd} / mo ({p.max_runs ?? '∞'} runs)
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;

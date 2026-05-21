import React from 'react';

export default function Ai_model({ user }) {
  return (
    <div>
      <div className="construction-banner">
        <span style={{ marginRight: '10px', fontSize: '1.1rem' }}>⚠️</span> 
        <strong>MODULE UNDER CONSTRUCTION</strong> — The predictive AI trading models are currently offline for training and backtesting.
      </div>
      
      <h2 style={{ fontFamily: "'DM Serif Display', serif", marginBottom: '20px' }}>
        AI Predictions & Analysis
      </h2>
      
      <p style={{ color: '#666', lineHeight: '1.6' }}>
        Check back later! This terminal will soon feature machine learning-driven price forecasts, automated risk assessments, and algorithmic trading signals based on the Finnhub data.
      </p>
    </div>
  );
}
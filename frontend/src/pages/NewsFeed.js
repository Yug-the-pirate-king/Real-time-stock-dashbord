import React from 'react';

export default function NewsFeed({ user }) {
  return (
    <div>
      <div className="construction-banner">
        <span style={{ marginRight: '10px', fontSize: '1.1rem' }}>⚠️</span> 
        <strong>MODULE UNDER CONSTRUCTION</strong> — The live financial news feed integration is currently being built.
      </div>
      
      <h2 style={{ fontFamily: "'DM Serif Display', serif", marginBottom: '20px' }}>
        Market News Feed
      </h2>
      
      <p style={{ color: '#666', lineHeight: '1.6' }}>
        Check back later! This section will eventually stream real-time market updates, global financial news, and sentiment analysis relevant to the assets in your depot.
      </p>
    </div>
  );
}
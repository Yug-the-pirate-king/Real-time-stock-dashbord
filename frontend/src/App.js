import React, { useState } from 'react';
import Login from './Login'; // <-- FIXED: Changed from './Frontend/Login' to './Login'

function App() {
  const [user, setUser] = useState(null); // Stores { user_id, username, balance }

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  // If no user is logged in, show the Login page
  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // If user IS logged in, show the actual simulator application dashboard
  return (
    <div style={{ padding: '20px' }}>
      <h1>Welcome back, {user.username}!</h1>
      <div style={{ padding: '20px', background: '#e2e8f0', borderRadius: '8px', display: 'inline-block' }}>
        <h3>💵 Virtual Wallet Balance: ${user.balance.toLocaleString()}</h3>
      </div>
      
      {/* Your future Dashboard, Simulator, and News Tab components go here */}
      <div style={{ marginTop: '30px' }}>
         <p>The login bridge works! Next up: Building the portfolio tracking system...</p>
      </div>
    </div>
  );
}

export default App;
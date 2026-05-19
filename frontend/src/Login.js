import React, { useState } from 'react';

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  // Function to handle Logging In
  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username) return;

    try {
      // FIXED: Added '/auth' prefix to match your backend router paths
      const response = await fetch(`http://127.0.0.1:8000/auth/login?username=${username}`, {
        method: 'POST',
      });
      const data = await response.json();

      if (response.ok) {
        setIsError(false);
        setMessage("Login successful!");
        // Pass the user data up to the main App state (saving user_id and balance)
        onLoginSuccess(data); 
      } else {
        setIsError(true);
        setMessage(data.detail || "Something went wrong");
      }
    } catch (error) {
      setIsError(true);
      setMessage("Cannot connect to backend server.");
    }
  };

  // Function to handle Registering a new account
  const handleRegister = async () => {
    if (!username) return;

    try {
      // FIXED: Cleared the double-fetch typo and pointed to /auth/create-user
      const response = await fetch(`http://127.0.0.1:8000/auth/create-user/${username}`, {
        method: 'POST',
      });
      
      const data = await response.json();

      if (response.ok) {
        setIsError(false);
        setMessage(`Account created! You can now log in.`);
      } else {
        setIsError(true);
        setMessage(data.detail || "Registration failed");
      }
    } catch (error) {
      setIsError(true);
      setMessage("Cannot connect to backend server.");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2>📈 Stock Simulator Login</h2>
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Enter Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
          />
          <div style={styles.buttonGroup}>
            <button type="submit" style={styles.loginBtn}>Log In</button>
            <button type="button" onClick={handleRegister} style={styles.registerBtn}>Register</button>
          </div>
        </form>
        
        {message && (
          <p style={{ ...styles.message, color: isError ? 'red' : 'green' }}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

// Simple CSS-in-JS styling for quick setup
const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#f0f2f5' },
  card: { padding: '40px', backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', textAlign: 'center', width: '320px' },
  input: { width: '100%', padding: '10px', marginBottom: '20px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' },
  buttonGroup: { display: 'flex', justifyContent: 'space-between' },
  loginBtn: { padding: '10px 20px', backgroundColor: '#007bff', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', width: '48%' },
  registerBtn: { padding: '10px 20px', backgroundColor: '#28a745', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', width: '48%' },
  message: { marginTop: '15px', fontWeight: 'bold' }
};
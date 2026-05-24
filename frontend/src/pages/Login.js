import React, { useState } from 'react';
import { API_BASE_URL } from '../config/api';

export default function Login({ onLoginSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');           // ← NEW
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    const cleanedUsername = username.trim();
    const cleanedPassword = password.trim();              // ← NEW

    if (!cleanedUsername || !cleanedPassword) {           // ← UPDATED
      setErrorMessage('Please enter a username and password.');
      return;
    }

    const endpoint = isRegistering ? 'create-user' : 'login';

    try {
      const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: cleanedUsername, password: cleanedPassword }) // ← UPDATED
      });

      const data = await response.json();

      if (response.ok) {
        onLoginSuccess({ id: data.id, username: data.username, balance: data.balance });
      } else {
        setErrorMessage(data.detail || 'Authentication failed.');
      }
    } catch (err) {
      setErrorMessage('Terminal engine offline.');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>{isRegistering ? 'Register Operator' : 'StockPulse Terminal'}</h2>
        <p style={styles.subtitle}>Initialize sandbox session via identity label.</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            type="text"
            placeholder="Enter Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
          />
          <input                                           // ← NEW BLOCK
            type="password"
            placeholder="Enter Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
          />
          <button type="submit" style={styles.submitBtn}>
            {isRegistering ? 'Initialize Identity →' : 'Connect Session →'}
          </button>
        </form>

        {errorMessage && <div style={styles.errorBox}>{errorMessage}</div>}

        <button
          onClick={() => { setIsRegistering(!isRegistering); setErrorMessage(''); setPassword(''); }} // ← password reset added
          style={styles.toggleBtn}
        >
          {isRegistering ? 'Return to secure log in' : 'New operator? Register terminal access'}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#fafaf8', fontFamily: "'DM Sans', sans-serif" },
  card: { padding: '40px', backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 24px rgba(0,0,0,0.03)', maxWidth: '380px', width: '100%', border: '1px solid #e8e8e3' },
  title: { fontFamily: "'DM Serif Display', serif", fontSize: '26px', color: '#0e0e0e', marginBottom: '6px', textAlign: 'center' },
  subtitle: { fontSize: '13px', color: '#787870', marginBottom: '24px', textAlign: 'center' },
  form: { display: 'flex', flexDirection: 'column', gap: '12px' },
  input: { padding: '14px', borderRadius: '8px', border: '1px solid #e8e8e3', fontSize: '14px', backgroundColor: '#fafaf8', outline: 'none', textAlign: 'center' },
  submitBtn: { padding: '14px', borderRadius: '8px', border: 'none', backgroundColor: '#0e0e0e', color: '#fff', cursor: 'pointer', fontWeight: '500', marginTop: '6px' },
  errorBox: { marginTop: '12px', padding: '10px', backgroundColor: '#fff5f5', color: '#e53e3e', fontSize: '13px', borderRadius: '6px', textAlign: 'center' },
  toggleBtn: { background: 'none', border: 'none', color: '#2d6b45', marginTop: '20px', cursor: 'pointer', width: '100%', textDecoration: 'underline', fontSize: '13px' }
};
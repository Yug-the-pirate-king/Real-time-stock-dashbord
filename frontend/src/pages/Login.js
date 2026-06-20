import React, { useState } from 'react';
import { API_BASE_URL } from '../config/api';

export default function Login({ onLoginSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    const cleanedUsername = username.trim();
    const cleanedPassword = password.trim();

    if (!cleanedUsername || !cleanedPassword) {
      setErrorMessage('Please enter a username and password.');
      return;
    }

    const endpoint = isRegistering ? 'create-user' : 'login';
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: cleanedUsername, password: cleanedPassword })
      });

      const data = await response.json();

      if (response.ok) {
        onLoginSuccess({ id: String(data.id), username: data.username, balance: data.balance });
      } else {
        setErrorMessage(data.detail || 'Authentication failed.');
      }
    } catch (err) {
      setErrorMessage('Terminal engine offline.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-root">
      <div className="login-left">
        <div className="login-left-content">
          <div className="login-brand">
            <span className="login-logo-dot" />
            <span className="login-logo-text">StockPulse</span>
          </div>
          <h1 className="login-headline">
            Trade the world.<br />
            <em>Know</em> your edge.
          </h1>
          <p className="login-subtitle">
            Real-time market data, multi-currency trading, and AI-powered signals —
            all in one terminal built for serious operators.
          </p>
          <div className="login-features">
            <div className="login-feature">
              <div className="login-feature-icon" style={{ background: 'var(--accent-subtle)', color: 'var(--accent-light)' }}>📈</div>
              <div>
                <div className="login-feature-title">Live Global Markets</div>
                <div className="login-feature-desc">Track equities across 20+ exchanges in real time.</div>
              </div>
            </div>
            <div className="login-feature">
              <div className="login-feature-icon" style={{ background: 'var(--amber-bg)', color: 'var(--amber)' }}>🌍</div>
              <div>
                <div className="login-feature-title">Multi-Currency Engine</div>
                <div className="login-feature-desc">Auto-convert INR, GBP, JPY, EUR, and more to USD instantly.</div>
              </div>
            </div>
            <div className="login-feature">
              <div className="login-feature-icon" style={{ background: 'var(--blue-bg)', color: 'var(--blue)' }}>🤖</div>
              <div>
                <div className="login-feature-title">AI Signals</div>
                <div className="login-feature-desc">Technical analysis with SMA crossovers and momentum scoring.</div>
              </div>
            </div>
          </div>
        </div>
        <div className="login-grid-bg" />
      </div>

      <div className="login-right">
        <div className="login-card">
          <div className="login-card-header">
            <h2 className="login-card-title">
              {isRegistering ? 'Create Account' : 'Welcome Back'}
            </h2>
            <p className="login-card-subtitle">
              {isRegistering
                ? 'Set up your operator identity to access the terminal.'
                : 'Enter your credentials to connect to the trading engine.'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="login-form-group">
              <label className="login-form-label">Username</label>
              <input
                type="text"
                className="login-form-input"
                placeholder="e.g. trader_01"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>
            <div className="login-form-group">
              <label className="login-form-label">Password</label>
              <input
                type="password"
                className="login-form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={isRegistering ? 'new-password' : 'current-password'}
              />
            </div>

            {errorMessage && (
              <div className="login-error">
                <span className="login-error-icon">!</span>
                {errorMessage}
              </div>
            )}

            <button
              type="submit"
              className="login-submit-btn"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="login-spinner" />
              ) : (
                <>
                  {isRegistering ? 'Create Account' : 'Connect Terminal'}
                  <span style={{ marginLeft: '6px' }}>→</span>
                </>
              )}
            </button>
          </form>

          <div className="login-divider">
            <span>or</span>
          </div>

          <button
            onClick={() => { setIsRegistering(!isRegistering); setErrorMessage(''); setPassword(''); }}
            className="login-toggle-btn"
          >
            {isRegistering ? 'Already have an account? Log in' : "New operator? Register access"}
          </button>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from "react";
import "../styles/landing.css";
import Antigravity from '../components/Antigravity';
import { AiOutlineStock } from "react-icons/ai";
import { FaBrain } from "react-icons/fa";
import { FaRegNewspaper } from "react-icons/fa";
import { IoIosPersonAdd } from "react-icons/io";
import { IoIosCall } from "react-icons/io";
import { MdOutlineMarkEmailUnread } from "react-icons/md";

export default function LandingPage({ onStart }) {
  const [scrolled, setScrolled] = useState(false);

  // Dynamic state hooks for live value changes
  const [tickers, setTickers] = useState([
    { sym: "BINANCE:BTCUSDT", price: 65000, change: 0, up: true },
    { sym: "AAPL", price: 213.42, change: 1.24, up: true },
    { sym: "TSLA", price: 176.88, change: -0.87, up: false },
    { sym: "NVDA", price: 891.30, change: 3.15, up: true },
    { sym: "MSFT", price: 418.50, change: 0.52, up: true },
    { sym: "AMZN", price: 184.20, change: -0.33, up: false },
    { sym: "GOOG", price: 167.45, change: 0.78, up: true },
    { sym: "META", price: 523.10, change: 1.90, up: true },
    { sym: "NFLX", price: 645.00, change: -1.02, up: false },
  ]);

  const [mockChartBars, setMockChartBars] = useState([55,35, 50, 42, 65, 58, 80, 72, 90, 95]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const socket = new WebSocket('wss://ws.finnhub.io?token=d87v551r01qmhakhgmd0d87v551r01qmhakhgmdg');

    // Subscribe to the tickers we want to track
    socket.addEventListener('open', function (event) {
      const symbolsToTrack = ["BINANCE:BTCUSDT", "AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOG", "META", "NFLX"];
      symbolsToTrack.forEach(sym => {
        socket.send(JSON.stringify({ 'type': 'subscribe', 'symbol': sym }));
      });
    });

    // Listen for live trades and update state
    socket.addEventListener('message', function (event) {
      const response = JSON.parse(event.data);
      if (response.type === 'trade') {
        const trades = response.data;
        trades.forEach(trade => {
          const tradeSymbol = trade.s;
          const tradePrice = trade.p;

          setTickers(prevTickers => prevTickers.map(t => {
            if (t.sym === tradeSymbol) {
              const priceDifference = tradePrice - t.price;
              if (priceDifference !== 0) {
                return {
                  ...t,
                  price: parseFloat(tradePrice.toFixed(2)),
                  change: parseFloat(priceDifference.toFixed(2)),
                  up: priceDifference >= 0
                };
              }
            }
            return t;
          }));
        });
      }
    });

    // Keep waving the chart vectors slowly inside the layout card preview block
    const chartInterval = setInterval(() => {
      setMockChartBars((prevBars) => {
        const next = [...prevBars];
        next.shift(); // Remove oldest data bar
        const variance = Math.floor(Math.random() * 20 - 10);
        const lastValue = prevBars[prevBars.length - 1];
        const newBarHeight = Math.max(20, Math.min(100, lastValue + variance));
        next.push(newBarHeight); // Push new simulated timeline data point
        return next;
      });
    }, 2500);

    // Cleanup on unmount
    return () => {
      socket.close();
      clearInterval(chartInterval);
    };
  }, []);

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  // Safe layout extraction selectors
  const previewApple = tickers.find((t) => t.sym === "AAPL") || tickers[0];

  return (
    <div style={{ backgroundColor: "var(--white)", minHeight: "100vh" }}>
      
      {/* HEADER NAV SYSTEM */}
      <nav className="sp-nav" style={{ boxShadow: scrolled ? "0 1px 20px rgba(0,0,0,0.06)" : "none" }}>
        <a href="#" className="sp-nav-logo" onClick={(e) => e.preventDefault()}>
          <span className="sp-logo-dot" />
          StockPulse
        </a>
        <ul className="sp-nav-links">
          <li><a href="#features" onClick={e => { e.preventDefault(); scrollToSection("features"); }}>Features</a></li>
          <li><a href="#how" onClick={e => { e.preventDefault(); scrollToSection("how"); }}>How it works</a></li>
          <li><a href="#contact" onClick={e => { e.preventDefault(); scrollToSection("contact"); }}>Contact</a></li>
        </ul>
        <button className="sp-btn-login" onClick={onStart}>Log in →</button>
      </nav>

      {/* HERO JUMBOTRON PANEL VIEW */}
      {/* Added position: relative and overflow: hidden to contain the absolute 3D background */}
      <section className="sp-hero" style={{ position: "relative", overflow: "hidden" }}>
        
        <div className="sp-hero-bg"/>
        
        {/* 3D BACKGROUND WRAPPER - Absolutely positioned to fill the hero */}
        <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", zIndex: 0 }}>
          <Antigravity
            count={1200}
            magnetRadius={12}
            ringRadius={7}
            waveSpeed={0.4}
            waveAmplitude={1}
            particleSize={1.5}
            lerpSpeed={0.05}
            color="#1a4a2e"
            autoAnimate
            particleVariance={1}
            rotationSpeed={0}
            depthFactor={1}
            pulseSpeed={3}
            particleShape="capsule"
            fieldStrength={10}
          />
        </div>

        <div className="sp-hero-grid" style={{ zIndex: 1, position: "relative", pointerEvents: "none" }} />
        
        {/* Added position relative and higher zIndex so text & buttons stay clickable on top */}
        <div className="sp-hero-content" style={{ position: "relative", zIndex: 10 }}>
          <div className="sp-hero-badge">
            <span className="sp-badge-pulse" />
            Live market intelligence
          </div>
          <h1 className="sp-h1">
            Markets move fast.<br />
            <em>Stay ahead</em> of them.
          </h1>
          <p className="sp-hero-sub">
            StockPulse combines real-time stock data, AI-powered price predictions,
            and curated financial news in one clean, powerful dashboard.
          </p>
          <div className="sp-hero-cta">
            <button onClick={onStart} className="sp-btn-primary">Get early access →</button>
            <button className="sp-btn-ghost" onClick={() => scrollToSection("features")}>Explore features ↓</button>
          </div>

          <div className="sp-hero-stats">
            <div>
              <div className="sp-stat-num">5,000+</div>
              <div className="sp-stat-label">Stocks tracked</div>
            </div>
            <div>
              <div className="sp-stat-num">94%</div>
              <div className="sp-stat-label">Prediction accuracy</div>
            </div>
            <div>
              <div className="sp-stat-num">Real-time</div>
              <div className="sp-stat-label">News feed</div>
            </div>
          </div>
        </div>
      </section>

      {/* INFINITE TAPE ROW */}
      <div className="sp-ticker-wrap">
        <div className="sp-ticker-inner">
          {[...tickers, ...tickers].map((t, i) => (
            <span className="sp-tick-item" key={i}>
              <span className="sp-tick-sym">{t.sym}</span>
              ${t.price.toFixed(2)}
              <span className={t.up ? "sp-tick-up" : "sp-tick-dn"}>
                {t.up ? "▲" : "▼"} {Math.abs(t.change).toFixed(2)}%
              </span>
            </span>
          ))}
        </div>
      </div>

      {/* CORE SPECIFICATIONS SECTION */}
      <section className="sp-section" id="features">
        <div className="sp-section-label">What's inside</div>
        <div className="sp-section-title">Everything you need to trade smarter.</div>
        <div className="sp-features-grid">
          <div className="sp-feature-card">
            <div className="sp-feature-icon sp-icon-green"><AiOutlineStock /></div>
            <div className="sp-feature-title">Live Stock Desk</div>
            <p className="sp-feature-desc">
              A full market overview at your fingertips. Track prices, volume, movers,
              and sector performance in real time — all in one clean interface.
            </p>
            <span className="sp-feature-tag">Real-time data</span>
          </div>
          <div className="sp-feature-card">
            <div className="sp-feature-icon sp-icon-amber"><FaBrain /></div>
            <div className="sp-feature-title">AI Price Predictor</div>
            <p className="sp-feature-desc">
              Our ML model analyses historical patterns, earnings data, and sentiment
              signals to forecast short-term price movements with confidence scores.
            </p>
            <span className="sp-feature-tag" style={{ background: "var(--amber-bg)", color: "var(--amber)" }}>AI-powered</span>
          </div>
          <div className="sp-feature-card">
            <div className="sp-feature-icon sp-icon-blue"><FaRegNewspaper /></div>
            <div className="sp-feature-title">Curated News Panel</div>
            <p className="sp-feature-desc">
              A dedicated news feed filtered to what matters. Market-moving headlines,
              earnings calls, analyst upgrades — surfaced instantly, without the noise.
            </p>
            <span className="sp-feature-tag" style={{ background: "var(--blue-bg)", color: "var(--blue)" }}>Live feed</span>
          </div>
        </div>
      </section>

      {/* HUD DASHBOARD CARD PREVIEW WRAP */}
      <section className="sp-section">
        <div className="sp-preview-wrap">
          <div className="sp-preview-text">
            <div className="sp-section-label">Inside the platform</div>
            <div className="sp-section-title" style={{ marginBottom: 20 }}>Your entire market view, one screen.</div>
            <p>
              From live charts to AI-generated forecasts and breaking news —
              StockPulse puts everything on a single dashboard so you can
              make faster, smarter decisions without switching tabs.
            </p>
            <button onClick={onStart} className="sp-btn-primary" style={{ width: "fit-content" }}>Get early access →</button>
          </div>
          
          <div className="sp-mockup">
            <div className="sp-mockup-bar">
              <div className="sp-dot" style={{ background: "#ff5f57" }} />
              <div className="sp-dot" style={{ background: "#febc2e" }} />
              <div className="sp-dot" style={{ background: "#28c840" }} />
            </div>
            <div className="sp-mockup-body">
              <div className="sp-mock-row">
                <div className="sp-mock-card">
                  <div className="sp-mock-label">{previewApple.sym}</div>
                  <div className="sp-mock-val" style={{ color: previewApple.up ? "#4ade80" : "#f87171" }}>
                    ${previewApple.price.toFixed(2)}
                  </div>
                  <div className="sp-mock-change" style={{ color: previewApple.up ? "#4ade80" : "#f87171" }}>
                    {previewApple.up ? "▲" : "▼"} {Math.abs(previewApple.change).toFixed(2)}% today
                  </div>
                </div>
                <div className="sp-mock-card">
                  <div className="sp-mock-label">AI Forecast</div>
                  <div className="sp-mock-val">$221.00</div>
                  <div className="sp-mock-change" style={{ color: "rgba(255,255,255,0.35)" }}>7-day target · 87% conf.</div>
                </div>
              </div>
              
              <div className="sp-mock-chart">
                {mockChartBars.map((h, i) => (
                  <div key={i} className="sp-bar" style={{
                    height: `${h}%`,
                    background: i === mockChartBars.length - 1 ? "rgba(45,107,69,1)" : "rgba(45,107,69,0.5)"
                  }} />
                ))}
              </div>
              
              <div className="sp-mock-news">
                {[
                  "Fed holds rates steady — markets rally on guidance",
                  "NVDA beats earnings, raises full-year guidance",
                  "Apple reportedly set to launch new AI chip in Q3",
                ].map((n, i) => (
                  <div key={i} className="sp-news-item">
                    <span className="sp-news-dot" />{n}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* OPERATIONS WORKFLOW METRIC STEPS */}
      <section className="sp-section sp-how-wrap" id="how">
        <div style={{ textAlign: "center" }}>
          <div className="sp-section-label">Process</div>
          <div className="sp-section-title" style={{ margin: "0 auto 60px", textAlign: "center" }}>
            Three steps to smarter investing.
          </div>
        </div>
        <div className="sp-steps-grid">
          {[
            { n: "1", title: "Create your account", desc: "Sign up in seconds. No credit card needed for early access." },
            { n: "2", title: "Build your watchlist", desc: "Add stocks you care about. The dashboard personalises instantly." },
            { n: "3", title: "Let the AI work", desc: "Get predictions, alerts, and curated news tailored to your portfolio." },
          ].map((s) => (
            <div className="sp-step" key={s.n}>
              <div className="sp-step-num">{s.n}</div>
              <div className="sp-step-title">{s.title}</div>
              <p className="sp-step-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CONTACT INFORMATION CARDS */}
      <section className="sp-section" id="contact">
          <div className="sp-contact-info">
            <div className="sp-section-label">Get in touch</div>
            <div className="sp-section-title" style={{ marginBottom: 16 }}>
              Questions? We'd love to hear from you.
            </div>
            <p>
              Whether you're a developer, investor, or just curious — reach out.
              We're actively onboarding early users and welcome all feedback.
            </p>
            <div className="sp-contact-detail">
              <div className="sp-contact-detail-icon"><IoIosPersonAdd /></div>
              Shah Yug Vipulbhai
            </div>
            <div className="sp-contact-detail">
              <div className="sp-contact-detail-icon"><IoIosCall /></div>
              +91 91371 43315
            </div>
            <div className="sp-contact-detail">
              <div className="sp-contact-detail-icon"><MdOutlineMarkEmailUnread /></div>
              yugshah197@gmail.com
            </div>
          </div>
      </section>

      {/* FOOTER BAR TERMINAL ACCENTS */}
      <footer className="sp-footer">
        <div className="sp-footer-logo">
          <span className="sp-logo-dot" />StockPulse
        </div>
        <ul className="sp-footer-links">
          <li><a href="#features" onClick={e => { e.preventDefault(); scrollToSection("features"); }}>Features</a></li>
          <li><a href="#how" onClick={e => { e.preventDefault(); scrollToSection("how"); }}>How it works</a></li>
          <li><a href="#contact" onClick={e => { e.preventDefault(); scrollToSection("contact"); }}>Contact</a></li>
        </ul>
        <div className="sp-footer-copy">© 2026 StockPulse. All rights reserved.</div>
      </footer>

    </div>
  );
}
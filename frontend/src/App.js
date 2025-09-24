import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './Home';
import About from './About';
import Login from './Login';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="main-nav">
          <div className="nav-logo">
            <Link to="/">
              <img src={`${process.env.PUBLIC_URL}/logo.png`} alt="Logo" />
            </Link>
          </div>
          <ul className="nav-links">
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/about">About</Link>
            </li>
          </ul>
          <div className="nav-login">
            <Link to="/login">로그인</Link>
          </div>
        </nav>

        <Routes>
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Home />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

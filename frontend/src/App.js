import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./Home";
import About from "./About";
import Login from "./Login";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);

  const handleRecommend = async () => {
    try {
      const response = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region: "E_capital", user_id: "e000004" })
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error fetching recommendation:", error);
      setResult({ error: "추천 요청 실패" });
    }
  };

  return (
    <Router>
      <div className="App">
        <nav className="main-nav">
          <div className="nav-logo">
            <Link to="/">TripMate</Link>
          </div>
          <ul className="nav-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/about">About</Link></li>
          </ul>
          <div className="nav-login">
            <Link to="/login">로그인</Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={
            <div>
              <h2>여행지 추천 테스트</h2>
              <button onClick={handleRecommend}>추천 받기</button>
              {result && (
                <pre>{JSON.stringify(result, null, 2)}</pre>
              )}
            </div>
          } />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
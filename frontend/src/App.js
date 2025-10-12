import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./Home";
import About from "./About";
import Login from "./Login";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const didFetch = useRef(false);

  const fetchRecommendations = async () => {
    setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  // 첫 로드 시 자동 호출
  useEffect(() => {
    if (!didFetch.current) {
      fetchRecommendations();
      didFetch.current = true;
    }
  }, []);

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
            <div className="recommend-container">
              <h2>오늘의 추천 여행지 ✈️</h2>

              {loading && <p>추천 불러오는 중...</p>}
              {result?.error && <p className="error-msg">{result.error}</p>}

              {result?.recommendations && (
                <div className="card-grid">
                  {result.recommendations.map((place, index) => (
                    <div key={index} className="card">
                      <img
                        src={`/images/${place.name}.jpg`}
                        alt={place.name}
                        onError={(e) => (e.target.src = "/images/default.jpg")}
                      />
                      <div className="card-content">
                        <h3>{place.name}</h3>
                        <p>{place.region}</p>
                        <p>⭐ {typeof place.score === "number" ? place.score.toFixed(3) : place.score}</p>
                      </div>
                    </div>
                  ))}
                </div>
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
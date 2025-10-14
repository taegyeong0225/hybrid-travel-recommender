import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import About from "./About";
import Login from "./Login";
import Signup from "./Signup"; // Import Signup component
import "./App.css";

function App() {
  console.log("렌더링 됨 - App 컴포넌트");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const didFetch = useRef(false);

  // useEffect(() => {
  //   let isMounted = true; // 언마운트된 이후 setState 방지
  
  //   const loadRecommendations = async () => {
  //     if (!didFetch.current && isMounted) {
  //       await fetchRecommendations();
  //       didFetch.current = true;
  //     }
  //   };
  
  //   loadRecommendations();
  
  //   // 클린업
  //   return () => {
  //     isMounted = false;
  //   };
  // }, []); // 상태를 의존성에 넣지 말기

  useEffect(() => {
    console.log("✅ useEffect triggered");
  
    let isMounted = true;
  
    const loadRecommendations = async () => {
      if (!didFetch.current && isMounted) {
        console.log("📡 fetching recommendations...");
        await fetchRecommendations();
        didFetch.current = true;
      }
    };
  
    loadRecommendations();
  
    return () => {
      console.log("🧹 cleanup triggered");
      isMounted = false;
    };
  }, []);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/recommend", { method: "POST" })
      if (!response.ok) throw new Error("Request failed");
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error fetching recommendation:", error);
      setResult({ error: "추천 요청 실패" });
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line no-unused-vars
  const fetchCurrentUser = async (token) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const userData = await response.json();
        setCurrentUser(userData);
      }
    } catch (error) {
      console.error("Failed to fetch user", error);
      // Token might be invalid, so clear it
      handleLogout();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
    // Navigate to home to prevent being on a protected route after logout
    window.location.href = '/';
  };

  const handlePlaceAction = async (endpoint, poi_id) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('로그인이 필요합니다.');
      return;
    }
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ poi_id: poi_id })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '요청 실패');
      }
      alert('처리되었습니다!');
    } catch (error) {
      console.error('Place action failed:', error);
      alert(`오류: ${error.message}`);
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
            {currentUser ? (
              <>
                <span className="welcome-msg">{currentUser.name}님</span>
                <button onClick={handleLogout} className="logout-btn">로그아웃</button>
              </>
            ) : (
              <>
                <Link to="/login">로그인</Link>
                <Link to="/signup" style={{ marginLeft: '10px' }}>회원가입</Link>
              </>
            )}
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
                        src={`${process.env.PUBLIC_URL}/images/${encodeURIComponent(place.name)}.jpg`}
                        alt={place.name}
                        onError={(e) => {
                          if (e.target.src !== "/images/default.jpg") {
                            e.target.onerror = null; // 무한 루프 방지
                            e.target.src = `${process.env.PUBLIC_URL}/images/default.jpg`;
                          }
                        }}
                      />
                      <div className="card-content">
                        <h3>{place.name}</h3>
                        <p>{place.region}</p>
                        <p>⭐ {typeof place.score === "number" ? place.score.toFixed(3) : place.score}</p>
                        {currentUser && (
                          <div className="card-actions">
                            <button onClick={() => handlePlaceAction('/api/favorites/add', place.name)}>찜하기</button>
                            <button onClick={() => handlePlaceAction('/api/visited/add', place.name)}>가봤어요</button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          } />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import About from "./About.jsx";
import Login from "./Login.jsx";
import Signup from "./Signup.jsx";
import MyPage from "./MyPage.jsx";
import TravelCarousel from "./TravelCarousel.jsx";
import "./App.css";

function App() {
  console.log("렌더링 됨 - App 컴포넌트");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const didFetch = useRef(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const isScrolled = window.scrollY > 10;
      if (isScrolled !== scrolled) {
        setScrolled(isScrolled);
      }
    };

    document.addEventListener('scroll', handleScroll);
    return () => {
      document.removeEventListener('scroll', handleScroll);
    };
  }, [scrolled]);

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

    const loadData = async () => {
      // Check if user is logged in
      const token = localStorage.getItem('token');
      if (token && isMounted) {
        await fetchCurrentUser(token);
      }

      // Load recommendations
      if (!didFetch.current && isMounted) {
        console.log("📡 fetching recommendations...");
        await fetchRecommendations();
        didFetch.current = true;
      }
    };

    loadData();

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

  const fetchCurrentUser = async (token) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const userData = await response.json();
        setCurrentUser(userData);
      } else {
        // Token is invalid, clear it
        handleLogout();
      }
    } catch (error) {
      console.error("Failed to fetch user", error);
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
        <nav className={`main-nav ${scrolled ? 'scrolled' : ''}`}>
          <div className="nav-logo">
            <Link to="/">
              <img src="/logo.png" alt="TripMate Logo" />
            </Link>
          </div>
          <ul className="nav-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/about">About</Link></li>
          </ul>
          <div className="nav-login">
            {currentUser ? (
              <>
                <Link to="/mypage" className="welcome-msg">{currentUser.name}님</Link>
                <button onClick={handleLogout} className="logout-btn">로그아웃</button>
              </>
            ) : (
                <Link to="/login">로그인</Link>
            )}
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={
              <div className="recommend-container">
                <h2>오늘의 추천 여행지 ✈️</h2>
                {loading && <p>추천 불러오는 중...</p>}
                {result?.error && <p className="error-msg">{result.error}</p>}
                {result?.recommendations && (
                  <TravelCarousel 
                    places={result.recommendations} 
                    currentUser={currentUser} 
                    handlePlaceAction={handlePlaceAction} 
                  />
                )}
              </div>
            } />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/mypage" element={<MyPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

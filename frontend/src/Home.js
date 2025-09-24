import React, { useState } from 'react';

function Home() {
  const [recommendations, setRecommendations] = useState('');

  const fetchRecommendations = async () => {
    try {
      const response = await fetch('http://localhost:8000/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ region: 'E_capital' }) // 예시 입력
      });
      const data = await response.json();
      setRecommendations(data.output); // FastAPI에서 반환하는 값
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  return (
    <header className="App-header">
      <h1>여행 추천 서비스</h1>
      <button onClick={fetchRecommendations}>추천 받기</button>
      <pre style={{ textAlign: 'left', marginTop: '20px' }}>
        {recommendations || '추천 결과가 여기 표시됩니다.'}
      </pre>
    </header>
  );
}

export default Home;
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './MyPage.css';

function MyPage() {
    const [user, setUser] = useState(null);
    const [favorites, setFavorites] = useState([]);
    const [visited, setVisited] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('favorites');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUserData = async () => {
            const token = localStorage.getItem('token');

            if (!token) {
                navigate('/login');
                return;
            }

            try {
                // Fetch user info
                const userResponse = await fetch('/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!userResponse.ok) {
                    throw new Error('인증 실패');
                }

                const userData = await userResponse.json();
                setUser(userData);

                // Fetch favorites
                const favResponse = await fetch('/api/favorites', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (favResponse.ok) {
                    const favData = await favResponse.json();
                    setFavorites(favData);
                }

                // Fetch visited places
                const visitedResponse = await fetch('/api/visited', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (visitedResponse.ok) {
                    const visitedData = await visitedResponse.json();
                    setVisited(visitedData);
                }

            } catch (error) {
                console.error('Error fetching user data:', error);
                alert('데이터를 불러오는 중 오류가 발생했습니다.');
                navigate('/login');
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, [navigate]);

    if (loading) {
        return (
            <div className="mypage-container">
                <div className="loading-spinner">로딩 중...</div>
            </div>
        );
    }

    if (!user) {
        return null;
    }

    return (
        <div className="mypage-container">
            <div className="mypage-header">
                <div className="user-profile">
                    <div className="profile-avatar">
                        {user.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="profile-info">
                        <h1>{user.name}님의 여행 기록</h1>
                        <p className="username">@{user.username}</p>
                        <p className="member-since">
                            가입일: {new Date(user.created_at).toLocaleDateString('ko-KR')}
                        </p>
                    </div>
                </div>

                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-number">{favorites.length}</div>
                        <div className="stat-label">즐겨찾기</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-number">{visited.length}</div>
                        <div className="stat-label">방문한 곳</div>
                    </div>
                </div>
            </div>

            <div className="mypage-content">
                <div className="tabs">
                    <button
                        className={`tab ${activeTab === 'favorites' ? 'active' : ''}`}
                        onClick={() => setActiveTab('favorites')}
                    >
                        즐겨찾기 ({favorites.length})
                    </button>
                    <button
                        className={`tab ${activeTab === 'visited' ? 'active' : ''}`}
                        onClick={() => setActiveTab('visited')}
                    >
                        방문한 곳 ({visited.length})
                    </button>
                </div>

                <div className="tab-content">
                    {activeTab === 'favorites' && (
                        <div className="places-grid">
                            {favorites.length === 0 ? (
                                <div className="empty-state">
                                    <p>아직 즐겨찾기한 장소가 없습니다.</p>
                                    <button onClick={() => navigate('/')} className="go-home-btn">
                                        여행지 둘러보기
                                    </button>
                                </div>
                            ) : (
                                favorites.map((fav) => (
                                    <div key={fav.id} className="place-card">
                                        <div className="place-header">
                                            <h3>{fav.poi_id}</h3>
                                            <span className="place-icon favorite">
                                                <i className="fa-solid fa-star"></i>
                                            </span>
                                        </div>
                                        <p className="place-date">
                                            추가일: {new Date(fav.created_at).toLocaleDateString('ko-KR')}
                                        </p>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'visited' && (
                        <div className="places-grid">
                            {visited.length === 0 ? (
                                <div className="empty-state">
                                    <p>아직 방문한 장소가 없습니다.</p>
                                    <button onClick={() => navigate('/')} className="go-home-btn">
                                        여행지 둘러보기
                                    </button>
                                </div>
                            ) : (
                                visited.map((visit) => (
                                    <div key={visit.id} className="place-card">
                                        <div className="place-header">
                                            <h3>{visit.poi_id}</h3>
                                            <span className="place-icon visited">
                                                <i className="fa-solid fa-check"></i>
                                            </span>
                                        </div>
                                        <p className="place-date">
                                            방문일: {new Date(visit.visited_at).toLocaleDateString('ko-KR')}
                                        </p>
                                        {visit.rating && (
                                            <div className="place-rating">
                                                평점: {'⭐'.repeat(Math.round(visit.rating))}
                                            </div>
                                        )}
                                        {visit.memo && (
                                            <p className="place-memo">{visit.memo}</p>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default MyPage;

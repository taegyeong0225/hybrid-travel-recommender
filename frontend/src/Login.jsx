import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Login.css';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        // Component mounts: disable scroll
        document.body.style.overflow = 'hidden';
        // Component unmounts: enable scroll
        return () => {
            document.body.style.overflow = 'auto';
        };
    }, []); // Empty dependency array ensures this runs only once on mount and unmount

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || '로그인에 실패했습니다.');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            
            window.location.href = '/';

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="login-page-container"> 
            <div className="login-box">
                <h2>다시 오신 걸 환영합니다</h2>
                <p className="login-subtitle">TripMate를 계속 이용하려면 로그인해 주세요.</p>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <input 
                            type="text" 
                            value={username} 
                            onChange={(e) => setUsername(e.target.value)} 
                            placeholder="아이디"
                            required
                        />
                    </div>
                    <div className="input-group">
                        <input 
                            type="password" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                            placeholder="비밀번호"
                            autoComplete="current-password"
                            required
                        />
                    </div>
                    {error && <p className="error-msg">{error}</p>}
                    <button type="submit" className="login-btn">로그인</button>
                </form>
                <div className="login-footer">
                    <p>아직 계정이 없으신가요? <Link to="/signup">회원가입</Link></p>
                </div>
            </div>
        </div>
    );
}

export default Login;

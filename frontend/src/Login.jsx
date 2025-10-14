import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './App.css';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

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
            
            // Navigate to home and force a reload to update App state
            window.location.href = '/';

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="login-container"> 
            <h2>로그인</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>아이디</label>
                    <input 
                        type="text" 
                        value={username} 
                        onChange={(e) => setUsername(e.target.value)} 
                    />
                </div>
                <div className="form-group">
                    <label>비밀번호</label>
                    <input 
                        type="password" 
                        value={password} 
                        placeholder="비밀번호"
                        autoComplete="current-password"
                        onChange={(e) => setPassword(e.target.value)} 
                    />
                </div>
                {error && <p className="error-msg">{error}</p>}
                <button type="submit">로그인</button>
            </form>
            <p>
                계정이 없으신가요? <Link to="/signup">회원가입</Link>
            </p>
        </div>
    );
}

export default Login;

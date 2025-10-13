import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './App.css'; // Assuming shared styles

function Signup() {
    const [name, setName] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!name || !username || !password) {
            setError('모든 필드를 입력해주세요.');
            return;
        }

        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, username, password }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || '회원가입에 실패했습니다.');
            }

            // Signup successful, navigate to login page
            navigate('/login');

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="login-container"> {/* Using login-container style for consistency */}
            <h2>회원가입</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>이름</label>
                    <input 
                        type="text" 
                        value={name} 
                        onChange={(e) => setName(e.target.value)} 
                    />
                </div>
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
                        onChange={(e) => setPassword(e.target.value)} 
                    />
                </div>
                {error && <p className="error-msg">{error}</p>}
                <button type="submit">가입하기</button>
            </form>
            <p>
                이미 계정이 있으신가요? <Link to="/login">로그인</Link>
            </p>
        </div>
    );
}

export default Signup;

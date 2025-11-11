import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Signup.css';

function Signup() {
    const [name, setName] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        // Component mounts: disable scroll
        document.body.style.overflow = 'hidden';
        // Component unmounts: enable scroll
        return () => {
            document.body.style.overflow = 'auto';
        };
    }, []);

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
                let data;
                try {
                    // 응답이 JSON 형식인지 확인
                    data = await response.json();
                } catch {
                    // 비어 있거나 JSON이 아닐 경우 대비
                    data = {};
                }
                throw new Error(data.detail || '회원가입에 실패했습니다.');
            }

            navigate('/login');

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="signup-page-container">
            <div className="signup-box">
                <h2>Create Your Account</h2>
                <p className="signup-subtitle">Join TripMate and start your journey</p>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <input 
                            type="text" 
                            value={name} 
                            onChange={(e) => setName(e.target.value)} 
                            placeholder="Name"
                            required
                        />
                    </div>
                    <div className="input-group">
                        <input 
                            type="text" 
                            value={username} 
                            onChange={(e) => setUsername(e.target.value)} 
                            placeholder="Username"
                            required
                        />
                    </div>
                    <div className="input-group">
                        <input 
                            type="password" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                            placeholder="Password"
                            required
                        />
                    </div>
                    {error && <p className="error-msg">{error}</p>}
                    <button type="submit" className="signup-btn">Sign Up</button>
                </form>
                <div className="signup-footer">
                    <p>Already have an account? <Link to="/login">Log In</Link></p>
                </div>
            </div>
        </div>
    );
}

export default Signup;

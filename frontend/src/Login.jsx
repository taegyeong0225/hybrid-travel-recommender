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
                <h2>Welcome Back</h2>
                <p className="login-subtitle">Sign in to continue to TripMate</p>
                <form onSubmit={handleSubmit}>
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
                            autoComplete="current-password"
                            required
                        />
                    </div>
                    {error && <p className="error-msg">{error}</p>}
                    <button type="submit" className="login-btn">Login</button>
                </form>
                <div className="login-footer">
                    <p>Don't have an account? <Link to="/signup">Sign Up</Link></p>
                </div>
            </div>
        </div>
    );
}

export default Login;

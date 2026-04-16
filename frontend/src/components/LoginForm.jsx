import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

function LoginForm() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        await client.post('/auth/register', { email, password });
        const res = await client.post('/auth/login', { email, password });
        login(res.data.access_token);
        navigate('/');
      } else {
        const res = await client.post('/auth/login', { email, password });
        login(res.data.access_token);
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred during authentication');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error && <div className="bg-neutral-900 border border-red-500 text-red-500 p-3 text-sm font-body">{error}</div>}
      
      <div className="flex flex-col gap-1">
        <label className="text-sm font-display text-neutral-400 uppercase tracking-widest">Email</label>
        <input 
          type="email" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="input-sharp"
          required 
        />
      </div>
      
      <div className="flex flex-col gap-1">
        <label className="text-sm font-display text-neutral-400 uppercase tracking-widest">Password</label>
        <input 
          type="password" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="input-sharp"
          required 
        />
      </div>
      
      <button type="submit" className="btn-primary mt-4" disabled={loading}>
        {loading ? 'Processing...' : (isRegister ? 'Register & Enter' : 'Authenticate')}
      </button>

      <button 
        type="button" 
        onClick={() => setIsRegister(!isRegister)} 
        className="text-xs text-neutral-500 mt-2 hover:text-white transition-colors uppercase font-display tracking-wider"
      >
        {isRegister ? 'Already have an account? Login instead.' : 'Need an account? Register instead.'}
      </button>
    </form>
  );
}

export default LoginForm;

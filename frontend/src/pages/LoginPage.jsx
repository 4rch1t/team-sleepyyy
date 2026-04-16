import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoginForm from '../components/LoginForm';

function LoginPage() {
  const { token } = useAuth();
  const navigate = useNavigate();

  if (token) {
    navigate('/');
    return null;
  }

  return (
    <div className="w-full h-[80vh] flex items-center justify-center">
      <div className="card-sharp w-full max-w-md">
        <h1 className="text-3xl mb-6 text-center">System Access</h1>
        <LoginForm />
      </div>
    </div>
  );
}

export default LoginPage;

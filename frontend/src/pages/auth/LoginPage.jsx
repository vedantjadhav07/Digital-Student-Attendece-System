import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, User, Eye, EyeOff, ArrowLeft, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import Card from '../../components/common/Card';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!username.trim() || !password) {
      setErrorMessage('Please enter both username and password.');
      return;
    }

    try {
      setIsLoading(true);
      const user = await login(username.trim(), password, rememberMe);
      toast.success(`Welcome back, ${user.name || user.username}!`);

      // Role-based redirection
      if (user.role === 'admin') {
        navigate('/admin');
      } else if (user.role === 'teacher') {
        navigate('/teacher');
      } else if (user.role === 'student') {
        navigate('/student');
      } else {
        navigate('/');
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Login failed. Please check your credentials.';
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick fill helper for convenience during testing
  const setDemoCredentials = (u, p) => {
    setUsername(u);
    setPassword(p);
    setErrorMessage('');
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 relative overflow-hidden bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text transition-colors">
      {/* Back to Home Link */}
      <div className="w-full max-w-md mb-4 flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-light-muted dark:text-dark-muted hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Labora Home
        </Link>
      </div>

      {/* Main Login Card */}
      <Card className="w-full max-w-md border-light-border dark:border-dark-border shadow-card p-6 sm:p-8 bg-light-surface dark:bg-dark-surface">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-lg bg-brand-deep p-2.5 mx-auto flex items-center justify-center shadow-subtle mb-3">
            <img src="/logo.svg" alt="Labora" className="w-full h-full object-contain" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-light-text dark:text-dark-text">
            Sign In to Labora
          </h2>
          <p className="text-xs text-light-muted dark:text-dark-muted mt-1">
            Smart Digital Attendance & Laboratory Control
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-medium animate-fadeIn">
            {errorMessage}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username / Roll Number"
            placeholder="e.g. admin, prof.sharma, 21CS001"
            icon={User}
            required
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••••••"
            icon={Lock}
            endIcon={showPassword ? EyeOff : Eye}
            onEndIconClick={() => setShowPassword(!showPassword)}
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <div className="flex items-center justify-between text-xs pt-1">
            <label className="flex items-center gap-2 cursor-pointer select-none text-light-muted dark:text-dark-muted">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded text-brand-teal focus:ring-brand-teal dark:bg-dark-surface dark:border-dark-border"
              />
              Remember this device
            </label>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="w-full mt-2"
          >
            Authenticate & Proceed
          </Button>
        </form>

        {/* Demo Credentials Quick-Select Pill */}
        <div className="mt-6 pt-5 border-t border-light-border dark:border-dark-border">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted mb-2 text-center">
            Quick Demo Accounts
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setDemoCredentials('admin', 'AdminSecurePassword!123')}
              className="px-2 py-1.5 rounded-lg border border-light-border dark:border-dark-border bg-light-surface hover:bg-slate-50 dark:bg-dark-surface dark:hover:bg-[#2a383a] hover:border-brand-teal dark:hover:border-brand-darkAction text-xs font-semibold text-light-text dark:text-dark-text transition-colors text-center shadow-subtle"
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('prof.sharma', 'TeacherPassword123')}
              className="px-2 py-1.5 rounded-lg border border-light-border dark:border-dark-border bg-light-surface hover:bg-slate-50 dark:bg-dark-surface dark:hover:bg-[#2a383a] hover:border-brand-teal dark:hover:border-brand-darkAction text-xs font-semibold text-light-text dark:text-dark-text transition-colors text-center shadow-subtle"
            >
              Teacher
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('21CS001', 'StudentPassword123')}
              className="px-2 py-1.5 rounded-lg border border-light-border dark:border-dark-border bg-light-surface hover:bg-slate-50 dark:bg-dark-surface dark:hover:bg-[#2a383a] hover:border-brand-teal dark:hover:border-brand-darkAction text-xs font-semibold text-light-text dark:text-dark-text transition-colors text-center shadow-subtle"
            >
              Student
            </button>
          </div>
        </div>
      </Card>

      {/* Security Footer Note */}
      <div className="mt-6 flex items-center gap-1.5 text-xs text-light-muted dark:text-dark-muted">
        <ShieldCheck className="w-4 h-4 text-brand-teal dark:text-brand-darkAction" />
        <span>End-to-end encrypted session with Argon2id credentials</span>
      </div>
    </div>
  );
}


import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sun, Moon, LogOut } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import Button from './Button';

export default function Navbar({ isPublic = false, onToggleSidebar, isSidebarCollapsed }) {
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getDashboardLink = () => {
    if (!user) return '/login';
    if (user.role === 'admin') return '/admin';
    if (user.role === 'teacher') return '/teacher';
    return '/student';
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-light-surface/95 dark:bg-dark-surface/95 border-b border-light-border dark:border-dark-border backdrop-blur-sm transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        {/* Left: Brand Logo & Title */}
        <div className="flex items-center gap-3">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="lg:hidden p-1.5 rounded-md text-light-muted dark:text-dark-muted hover:bg-light-secondary dark:hover:bg-dark-secondary mr-1"
              aria-label="Toggle Navigation"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          )}

          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-md bg-brand-deep p-1 flex items-center justify-center shrink-0">
              <img src="/logo.svg" alt="Labora" className="w-full h-full object-contain" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-light-text dark:text-dark-text">
                Labora
              </span>
              <span className="text-[10px] font-medium tracking-wider text-light-muted dark:text-dark-muted uppercase -mt-1 hidden sm:block">
                Smart Digital Attendance
              </span>
            </div>
          </Link>
        </div>

        {/* Center: Public Navigation Links */}
        {isPublic && (
          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-light-muted dark:text-dark-muted">
            <a href="#home" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">Home</a>
            <a href="#features" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">How It Works</a>
            <a href="#contact" className="hover:text-brand-teal dark:hover:text-brand-darkAction transition-colors">Contact</a>
          </nav>
        )}

        {/* Right: Actions */}
        <div className="flex items-center gap-2.5">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            type="button"
            className="p-1.5 rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text hover:bg-light-secondary dark:hover:bg-dark-secondary transition-colors"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-brand-teal" />
            )}
          </button>

          {isPublic ? (
            isAuthenticated ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate(getDashboardLink())}
              >
                Go to Dashboard
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate('/login')}
              >
                Sign In
              </Button>
            )
          ) : (
            user && (
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-semibold text-light-text dark:text-dark-text leading-tight">
                    {user.name || user.username}
                  </span>
                  <span className="text-[10px] font-medium uppercase tracking-wider text-brand-teal dark:text-brand-darkAction">
                    {user.role}
                  </span>
                </div>
                <div className="w-7 h-7 rounded-md bg-brand-deep text-white text-xs font-bold flex items-center justify-center">
                  {(user.name || user.username || 'U')[0].toUpperCase()}
                </div>
                <button
                  onClick={handleLogout}
                  title="Logout"
                  className="p-1.5 rounded-md text-light-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )
          )}
        </div>
      </div>
    </header>
  );
}

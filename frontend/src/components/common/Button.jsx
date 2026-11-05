import React from 'react';
import { Loader2 } from 'lucide-react';

export default function Button({
  children,
  variant = 'primary', // 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size = 'md',        // 'sm' | 'md' | 'lg'
  isLoading = false,
  disabled = false,
  icon: Icon,
  className = '',
  type = 'button',
  onClick,
  ...props
}) {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-brand-teal dark:focus:ring-brand-darkAction dark:focus:ring-offset-dark-bg disabled:opacity-50 disabled:cursor-not-allowed';

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5 h-8 gap-1.5',
    md: 'text-sm px-4 py-2 h-9 gap-2',
    lg: 'text-base px-5 py-2.5 h-11 gap-2.5',
  };

  const variantClasses = {
    primary: 'bg-brand-teal hover:bg-[#2E6561] text-white dark:bg-brand-darkAction dark:hover:bg-[#8EC4B8] dark:text-[#151D1E] font-semibold shadow-subtle',
    secondary: 'bg-white hover:bg-light-secondary text-light-text border border-light-border dark:bg-dark-surface dark:hover:bg-dark-secondary dark:text-dark-text dark:border-dark-border shadow-subtle',
    outline: 'bg-transparent border border-brand-teal text-brand-teal hover:bg-brand-soft/20 dark:border-brand-darkAction dark:text-brand-darkAction dark:hover:bg-brand-teal/20',
    ghost: 'bg-transparent text-light-muted hover:text-light-text hover:bg-light-secondary dark:text-dark-muted dark:hover:text-dark-text dark:hover:bg-dark-secondary',
    danger: 'bg-red-600 hover:bg-red-700 text-white shadow-subtle',
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : Icon ? (
        <Icon className={`${size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} text-current shrink-0`} />
      ) : null}
      <span className="text-current inline-flex items-center gap-1.5">{children}</span>
    </button>
  );
}

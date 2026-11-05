import React from 'react';

export default function Badge({
  children,
  variant = 'neutral', // 'teal' | 'success' | 'warning' | 'danger' | 'neutral' | 'purple' | 'info'
  size = 'md', // 'sm' | 'md'
  className = '',
  dot = false,
}) {
  const variantStyles = {
    teal: 'bg-brand-soft/25 text-brand-deep dark:bg-brand-teal/20 dark:text-brand-darkAction border-brand-soft/40 dark:border-brand-teal/40',
    purple: 'bg-brand-soft/25 text-brand-deep dark:bg-brand-teal/20 dark:text-brand-darkAction border-brand-soft/40 dark:border-brand-teal/40',
    success: 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60',
    warning: 'bg-amber-50 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 border-amber-200 dark:border-amber-800/60',
    danger: 'bg-rose-50 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300 border-rose-200 dark:border-rose-800/60',
    info: 'bg-sky-50 text-sky-800 dark:bg-sky-950/50 dark:text-sky-300 border-sky-200 dark:border-sky-800/60',
    neutral: 'bg-light-secondary text-light-text dark:bg-dark-secondary dark:text-dark-text border-light-border dark:border-dark-border',
  };

  const dotColors = {
    teal: 'bg-brand-teal dark:bg-brand-darkAction',
    purple: 'bg-brand-teal dark:bg-brand-darkAction',
    success: 'bg-emerald-600',
    warning: 'bg-amber-600',
    danger: 'bg-rose-600',
    info: 'bg-sky-600',
    neutral: 'bg-light-muted dark:bg-dark-muted',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 rounded',
    md: 'text-xs px-2.5 py-0.5 rounded-md',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium border ${sizeStyles[size]} ${variantStyles[variant] || variantStyles.neutral} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant] || dotColors.neutral}`} />}
      {children}
    </span>
  );
}

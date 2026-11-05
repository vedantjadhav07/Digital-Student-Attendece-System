import React from 'react';

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeType = 'teal', // 'teal' | 'success' | 'warning' | 'danger'
  className = '',
}) {
  const badgeClasses = {
    teal: 'bg-brand-soft/20 text-brand-teal dark:bg-brand-teal/20 dark:text-brand-darkAction',
    success: 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
    warning: 'bg-amber-500/10 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300',
    danger: 'bg-rose-500/10 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300',
  };

  return (
    <div
      className={`p-5 rounded-lg border bg-light-surface dark:bg-dark-surface border-light-border dark:border-dark-border shadow-card transition-all ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted">
          {title}
        </span>
        {Icon && (
          <div className="w-8 h-8 rounded-md bg-light-secondary dark:bg-dark-secondary text-brand-teal dark:text-brand-darkAction flex items-center justify-center">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2.5">
        <span className="text-2xl font-bold tracking-tight text-light-text dark:text-dark-text">
          {value !== undefined && value !== null ? value : '--'}
        </span>
        {badgeText && (
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded ${badgeClasses[badgeType]}`}
          >
            {badgeText}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-1.5 text-xs text-light-muted dark:text-dark-muted">
          {subtitle}
        </p>
      )}
    </div>
  );
}

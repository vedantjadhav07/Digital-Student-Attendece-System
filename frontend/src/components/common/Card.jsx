import React from 'react';

export default function Card({
  children,
  className = '',
  title,
  subtitle,
  action,
  headerClassName = '',
  bodyClassName = '',
  footer,
  footerClassName = '',
  hover = false,
  ...props
}) {
  return (
    <div
      className={`rounded-lg border bg-light-surface dark:bg-dark-surface border-light-border dark:border-dark-border shadow-card transition-all duration-150 ${
        hover ? 'hover:border-brand-teal/40 dark:hover:border-brand-darkAction/40' : ''
      } ${className}`}
      {...props}
    >
      {(title || subtitle || action) && (
        <div
          className={`px-5 py-4 border-b border-light-border dark:border-dark-border flex items-center justify-between gap-4 ${headerClassName}`}
        >
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-light-text dark:text-dark-text tracking-tight">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-light-muted dark:text-dark-muted mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="flex items-center gap-2 shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-5 ${bodyClassName}`}>{children}</div>
      {footer && (
        <div
          className={`px-5 py-3 bg-light-secondary/60 dark:bg-dark-secondary/60 border-t border-light-border dark:border-dark-border ${footerClassName}`}
        >
          {footer}
        </div>
      )}
    </div>
  );
}

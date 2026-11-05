import React from 'react';
import { FolderOpen } from 'lucide-react';
import Button from './Button';

export default function EmptyState({
  icon: Icon = FolderOpen,
  title = 'No records found',
  description = 'There are no records to display here yet.',
  actionLabel,
  onAction,
  className = '',
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-light-border dark:border-dark-border bg-light-surface/40 dark:bg-dark-surface/40 ${className}`}
    >
      <div className="w-10 h-10 rounded-md bg-light-secondary dark:bg-dark-secondary text-brand-teal dark:text-brand-darkAction flex items-center justify-center mb-3">
        <Icon className="w-5 h-5" />
      </div>
      <h4 className="text-sm font-semibold text-light-text dark:text-dark-text">
        {title}
      </h4>
      <p className="text-xs text-light-muted dark:text-dark-muted max-w-sm mt-1">
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction} className="mt-4">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

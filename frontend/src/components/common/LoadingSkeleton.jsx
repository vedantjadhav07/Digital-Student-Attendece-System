import React from 'react';

export function Skeleton({ className = '' }) {
  return (
    <div
      className={`animate-pulse bg-light-secondary dark:bg-dark-secondary rounded-md ${className}`}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="p-5 rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface space-y-3">
      <div className="flex justify-between items-center">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-8 w-8 rounded-md" />
      </div>
      <Skeleton className="h-7 w-20" />
      <Skeleton className="h-3 w-36" />
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div className="rounded-lg border border-light-border dark:border-dark-border overflow-hidden p-4 space-y-3 bg-light-surface dark:bg-dark-surface">
      <div className="flex gap-4 border-b border-light-border dark:border-dark-border pb-3">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-1.5">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export default function LoadingSkeleton({ type = 'card', count = 3 }) {
  if (type === 'table') {
    return <TableSkeleton />;
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

import React from 'react';

export default function Table({
  headers = [],
  children,
  className = '',
  emptyText = 'No records found',
  isEmpty = false,
}) {
  return (
    <div className={`w-full overflow-x-auto rounded-lg border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-subtle ${className}`}>
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-light-secondary dark:bg-dark-secondary border-b border-light-border dark:border-dark-border text-xs uppercase font-semibold text-light-muted dark:text-dark-muted tracking-wider">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className={`px-4 py-3 ${h.className || ''}`}>
                {h.label || h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-light-border dark:divide-dark-border font-normal text-light-text dark:text-dark-text">
          {isEmpty ? (
            <tr>
              <td
                colSpan={headers.length || 1}
                className="px-4 py-8 text-center text-sm text-light-muted dark:text-dark-muted"
              >
                {emptyText}
              </td>
            </tr>
          ) : (
            children
          )}
        </tbody>
      </table>
    </div>
  );
}

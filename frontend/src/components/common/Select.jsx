import React, { forwardRef } from 'react';

const Select = forwardRef(({
  label,
  error,
  helperText,
  icon: Icon,
  options = [],
  children,
  className = '',
  wrapperClassName = '',
  required = false,
  ...props
}, ref) => {
  return (
    <div className={`w-full flex flex-col gap-1.5 ${wrapperClassName}`}>
      {label && (
        <label className="text-xs font-medium text-light-text dark:text-dark-text flex items-center justify-between">
          <span>
            {label} {required && <span className="text-brand-teal dark:text-brand-darkAction">*</span>}
          </span>
        </label>
      )}
      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3 text-light-muted dark:text-dark-muted pointer-events-none flex items-center">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <select
          ref={ref}
          className={`w-full rounded-lg border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text text-sm h-9 px-3 transition-colors outline-none focus:ring-1 focus:ring-brand-teal focus:border-brand-teal dark:focus:ring-brand-darkAction dark:focus:border-brand-darkAction appearance-none cursor-pointer ${
            Icon ? 'pl-9' : ''
          } pr-8 ${
            error
              ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
              : 'border-light-border dark:border-dark-border hover:border-brand-teal/50 dark:hover:border-brand-darkAction/50'
          } ${className}`}
          {...props}
        >
          {children ||
            options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text">
                {opt.label}
              </option>
            ))}
        </select>
        <div className="absolute right-3 pointer-events-none text-light-muted dark:text-dark-muted">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      {error && <p className="text-xs text-red-600 dark:text-red-400 font-medium">{error}</p>}
      {!error && helperText && <p className="text-xs text-light-muted dark:text-dark-muted">{helperText}</p>}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;

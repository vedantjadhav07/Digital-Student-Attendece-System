import React, { forwardRef } from 'react';

const Input = forwardRef(({
  label,
  error,
  helperText,
  icon: Icon,
  endIcon: EndIcon,
  onEndIconClick,
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
        <input
          ref={ref}
          className={`w-full rounded-lg border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text placeholder:text-light-muted/60 dark:placeholder:text-dark-muted/60 text-sm h-9 px-3 transition-colors outline-none focus:ring-1 focus:ring-brand-teal focus:border-brand-teal dark:focus:ring-brand-darkAction dark:focus:border-brand-darkAction ${
            Icon ? 'pl-9' : ''
          } ${
            EndIcon ? 'pr-9' : ''
          } ${
            error
              ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
              : 'border-light-border dark:border-dark-border hover:border-brand-teal/50 dark:hover:border-brand-darkAction/50'
          } ${className}`}
          {...props}
        />
        {EndIcon && (
          <button
            type="button"
            tabIndex={-1}
            onClick={onEndIconClick}
            className="absolute right-3 text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text transition-colors flex items-center"
          >
            <EndIcon className="w-4 h-4" />
          </button>
        )}
      </div>
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 font-medium">{error}</p>
      )}
      {!error && helperText && (
        <p className="text-xs text-light-muted dark:text-dark-muted">{helperText}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;

import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  maxWidth = 'max-w-lg', // 'max-w-md' | 'max-w-lg' | 'max-w-2xl' | 'max-w-4xl'
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-brand-ink/50 dark:bg-black/70 backdrop-blur-[2px] transition-opacity"
        onClick={onClose}
      />

      {/* Modal Box */}
      <div
        className={`relative w-full ${maxWidth} bg-light-surface dark:bg-dark-surface border border-light-border dark:border-dark-border rounded-xl shadow-modal overflow-hidden z-10 my-8`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-light-border dark:border-dark-border">
          <div>
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text tracking-tight">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-light-muted dark:text-dark-muted mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-light-muted hover:text-light-text hover:bg-light-secondary dark:text-dark-muted dark:hover:text-dark-text dark:hover:bg-dark-secondary transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 max-h-[calc(85vh-130px)] overflow-y-auto">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-5 py-3 bg-light-secondary/60 dark:bg-dark-secondary/60 border-t border-light-border dark:border-dark-border flex items-center justify-end gap-2.5">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

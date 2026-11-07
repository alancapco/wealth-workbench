'use client';

import React, { useEffect, useRef } from 'react';

interface AccessibleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

/**
 * WCAG-compliant modal dialog with focus trap and keyboard navigation.
 * Authority: Design P-020 overlays, NFR-08/09 accessibility
 */
export function AccessibleDialog({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  size = 'md',
}: AccessibleDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-7xl',
  };

  // Focus management and keyboard handling
  useEffect(() => {
    if (isOpen) {
      // Store previous focus
      previousFocusRef.current = document.activeElement as HTMLElement;

      // Focus dialog
      dialogRef.current?.focus();

      // Prevent body scroll
      document.body.style.overflow = 'hidden';

      // Keyboard event handler
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }

        // Focus trap
        if (e.key === 'Tab' && dialogRef.current) {
          const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      };

      document.addEventListener('keydown', handleKeyDown);

      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
        // Restore focus
        previousFocusRef.current?.focus();
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby={description ? 'dialog-description' : undefined}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div
          ref={dialogRef}
          className={`relative bg-white rounded-lg shadow-2xl w-full ${sizeClasses[size]} max-h-[90vh] flex flex-col`}
          tabIndex={-1}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-black text-white rounded-t-lg">
            <div>
              <h2 id="dialog-title" className="text-xl font-semibold">
                {title}
              </h2>
              {description && (
                <p id="dialog-description" className="text-sm text-gray-300 mt-1">
                  {description}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-300 text-2xl leading-none w-8 h-8 flex items-center justify-center"
              aria-label="Close dialog"
            >
              ×
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-auto px-6 py-6">{children}</div>

          {/* Footer */}
          {footer && (
            <div className="px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

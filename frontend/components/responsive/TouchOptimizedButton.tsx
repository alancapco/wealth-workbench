// Touch-optimized button with larger tap targets (min 44x44px)
// Authority: U-014, REMEDIATION_02_Product_Design.md §7 accessibility requirements

import { ReactNode, ButtonHTMLAttributes } from 'react';

interface TouchOptimizedButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
  fullWidth?: boolean;
}

export default function TouchOptimizedButton({
  children,
  variant = 'primary',
  fullWidth = false,
  className = '',
  ...props
}: TouchOptimizedButtonProps) {
  const baseClasses = 'btn-touch focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-capco-black text-white hover:bg-capco-gray-800 focus:ring-capco-gray-600',
    secondary: 'bg-capco-gray-100 text-capco-black hover:bg-capco-gray-200 focus:ring-capco-gray-400',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  const widthClass = fullWidth ? 'w-full mobile-full-button' : '';

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${widthClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

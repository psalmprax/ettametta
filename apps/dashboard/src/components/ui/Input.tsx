"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  readonly label?: string;
  readonly error?: string;
  readonly icon?: React.ReactNode;
  readonly variant?: "default" | "minimal";
  readonly fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, variant = "default", fullWidth = false, ...props }, ref) => {
    const baseStyles = "w-full font-medium transition-all duration-200 rounded-2xl";
    
    const variants = {
      default: `bg-white border border-slate-200 px-4 py-3 text-slate-900 placeholder:text-slate-400 
        focus:border-violet-400 focus:outline-none focus:ring-4 focus:ring-violet-400/15 shadow-sm`,
      minimal: `bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-slate-900 placeholder:text-slate-400 
        focus:border-violet-400 focus:outline-none focus:ring-4 focus:ring-violet-400/15`,
    };

    const containerStyles = cn(
      "relative",
      fullWidth && "w-full",
      className
    );

    const generatedId = React.useId();
    const id = props.id || generatedId;

    return (
      <div className={containerStyles}>
        {label && (
          <label htmlFor={id} className="block text-sm font-semibold text-slate-700 mb-2">
            {label}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            id={id}
            className={cn(
              baseStyles,
              variants[variant],
              icon && "pl-12",
              error && "border-rose-400/80 focus:border-rose-400 focus:ring-rose-400/20"
            )}
            {...props}
          />
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
              {icon}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-2 text-sm font-medium text-rose-500">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

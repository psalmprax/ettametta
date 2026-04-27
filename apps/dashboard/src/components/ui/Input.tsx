/** @jsxImportSource react */
"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  variant?: "default" | "cyber" | "minimal";
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, variant = "default", fullWidth = false, ...props }, ref) => {
    const baseStyles = "w-full font-medium transition-all duration-300";
    
    const variants = {
      default: `bg-black/60 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-zinc-600 
        focus:border-cyan-400/50 focus:outline-none focus:ring-2 focus:ring-cyan-400/20`,
      cyber: `bg-zinc-950 border border-white/5 rounded-xl px-4 py-3 text-white placeholder:text-zinc-700 
        focus:border-cyan-400 focus:outline-none cyber-border`,
      minimal: `bg-transparent border-b border-white/20 rounded-none px-0 py-2 text-white placeholder:text-zinc-600 
        focus:border-cyan-400 focus:outline-none`,
    };

    const containerStyles = cn(
      "relative",
      fullWidth && "w-full",
      className
    );

    return (
      <div className={containerStyles}>
        {label && (
          <label className="block text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">
            {label}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            className={cn(
              baseStyles,
              variants[variant],
              icon && "pl-12",
              error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20"
            )}
            {...props}
          />
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600">
              {icon}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-2 text-xs font-bold text-red-500">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

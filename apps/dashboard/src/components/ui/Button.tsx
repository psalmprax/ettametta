import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md" | "lg" | "xl";
  isLoading?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  rounded?: "md" | "lg" | "xl" | "full";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = "primary",
    size = "md",
    isLoading = false,
    fullWidth = false,
    icon,
    iconPosition = "left",
    rounded = "lg",
    children,
    disabled,
    ...props
  }, ref) => {
    const baseStyles = "relative font-semibold transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500/20";
    
    const radius = {
      md: "rounded-lg",
      lg: "rounded-xl",
      xl: "rounded-2xl",
      full: "rounded-full",
    };

    const variants = {
      primary: `bg-gradient-to-r from-indigo-600 to-indigo-700 text-white hover:from-indigo-700 hover:to-indigo-800 shadow-md hover:shadow-lg border border-indigo-600/20 hover:border-indigo-400/30`,
      secondary: "bg-white text-slate-800 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-sm hover:shadow-md",
      outline: "bg-transparent text-slate-700 border border-slate-300 hover:bg-slate-50 hover:border-slate-400 shadow-sm",
      ghost: "bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 border-transparent",
      danger: "bg-gradient-to-r from-rose-500 to-rose-600 text-white hover:from-rose-600 hover:to-rose-700 shadow-md hover:shadow-lg border border-rose-500/20",
    };

    const sizes = {
      sm: "px-4 py-2 text-xs gap-2",
      md: "px-6 py-3 text-sm gap-3",
      lg: "px-8 py-4 text-base gap-4",
      xl: "px-10 py-5 text-lg gap-5",
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          radius[rounded],
          sizes[size],
          fullWidth && "w-full",
          isLoading && "cursor-wait",
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <div className="w-5 h-5 border-2 border-white/50 border-t-transparent rounded-full animate-spin" />
        ) : icon && iconPosition === "left" ? (
          <span className="flex-shrink-0">{icon}</span>
        ) : null}
        <span className="whitespace-nowrap">{children}</span>
        {!isLoading && icon && iconPosition === "right" ? (
          <span className="flex-shrink-0">{icon}</span>
        ) : null}
      </button>
    );
  }
);

Button.displayName = "Button";

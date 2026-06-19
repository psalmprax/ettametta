import React from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  readonly variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  readonly size?: "sm" | "md" | "lg" | "xl";
  readonly isLoading?: boolean;
  readonly fullWidth?: boolean;
  readonly icon?: React.ReactNode;
  readonly iconPosition?: "left" | "right";
  readonly rounded?: "md" | "lg" | "xl" | "2xl" | "full";
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
    rounded = "xl",
    children,
    disabled,
    ...props
  }, ref) => {
    const baseStyles = "relative font-semibold transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500/20";
    
    const radius = {
      md: "rounded-lg",
      lg: "rounded-xl",
      xl: "rounded-2xl",
      "2xl": "rounded-3xl",
      full: "rounded-full",
    };

    const variants = {
      primary: `bg-primary text-white hover:bg-primary-hover shadow-lg shadow-cyan-900/20 border border-white/10`,
      secondary: "bg-slate-900 text-white border border-white/10 hover:bg-slate-800 hover:border-white/20 shadow-sm",
      outline: "bg-transparent text-white border border-white/20 hover:bg-white/5 shadow-sm",
      ghost: "bg-transparent text-slate-400 hover:bg-white/5 hover:text-white border-transparent",
      danger: `bg-error text-white hover:bg-rose-700 shadow-lg shadow-rose-900/20 border border-white/10`,
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
          <span className="shrink-0">{icon}</span>
        ) : null}
        <span className="whitespace-nowrap">{children}</span>
        {!isLoading && icon && iconPosition === "right" ? (
          <span className="shrink-0">{icon}</span>
        ) : null}
      </button>
    );
  }
);

Button.displayName = "Button";

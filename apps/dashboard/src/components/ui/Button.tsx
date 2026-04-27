import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "xl";
  isLoading?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
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
    children,
    disabled,
    ...props
  }, ref) => {
    const baseStyles = "relative font-bold uppercase tracking-wide transition-all duration-300 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed border rounded-full";
    
    const variants = {
      primary: "bg-cyan-500 text-black border-cyan-500 shadow-[0_0_20px_rgba(0,251,251,0.2)] hover:shadow-[0_0_35px_rgba(0,251,251,0.4)] hover:scale-[1.02] overflow-hidden",
      secondary: "bg-white/5 text-white border-white/10 hover:border-cyan-400/50 hover:text-cyan-400 hover:bg-white/10",
      ghost: "bg-transparent text-white border-transparent hover:bg-white/5 hover:text-cyan-400",
      danger: "bg-red-500 text-white border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.2)] hover:shadow-[0_0_30px_rgba(239,68,68,0.4)] overflow-hidden",
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
          sizes[size],
          fullWidth && "w-full",
          isLoading && "cursor-wait",
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
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

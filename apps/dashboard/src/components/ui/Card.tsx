import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "glass" | "solid" | "elevated" | "cyber";
  withBorder?: boolean;
  glow?: "cyan" | "violet" | "none";
  className?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "glass", withBorder = true, glow = "none", children, ...props }, ref) => {
    const baseStyles = "relative overflow-hidden";
    
    const variants = {
      glass: "surface-glass",
      solid: "surface-solid",
      elevated: "surface-elevated",
      cyber: "cyber-border surface-solid",
    };

    const glowStyles = {
      cyan: "shadow-[0_0_30px_rgba(0,251,251,0.15)] hover:shadow-[0_0_45px_rgba(0,251,251,0.25)]",
      violet: "shadow-[0_0_30px_rgba(208,91,255,0.15)] hover:shadow-[0_0_45px_rgba(208,91,255,0.25)]",
      none: "",
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          withBorder && "border border-white/10",
          glowStyles[glow],
          "transition-all duration-300",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

export const CardHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-b border-white/5", className)} {...props}>
    {children}
  </div>
);

export const CardBody = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6", className)} {...props}>
    {children}
  </div>
);

export const CardFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-t border-white/5", className)} {...props}>
    {children}
  </div>
);

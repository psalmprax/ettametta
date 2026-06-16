import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "solid" | "elevated" | "subtle" | "accent";
  withBorder?: boolean;
  className?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "solid", withBorder = true, children, ...props }, ref) => {
    const baseStyles = "relative overflow-hidden transition-all duration-300 rounded-2xl";
    
    const variants = {
      solid: "bg-slate-900/50 border border-white/5 shadow-sm hover:border-white/10",
      elevated: "bg-slate-900 border border-white/10 shadow-lg",
      subtle: "bg-black/20 border border-white/5 hover:border-white/10",
      accent: "bg-cyan-400/5 border border-cyan-400/20 shadow-sm",
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          !withBorder && "border-none shadow-none",
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

const CardHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-b border-white/5", className)} {...props}>
    {children}
  </div>
);

const CardBody = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6", className)} {...props}>
    {children}
  </div>
);

const CardFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-t border-white/5", className)} {...props}>
    {children}
  </div>
);
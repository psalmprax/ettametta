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
      solid: "bg-white border border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300",
      elevated: "bg-white border border-slate-100 shadow-md hover:shadow-lg",
      subtle: "bg-slate-50 border border-transparent hover:border-slate-200",
      accent: "bg-indigo-50 border border-indigo-100 shadow-sm hover:shadow-md",
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

export const CardHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-b border-slate-100", className)} {...props}>
    {children}
  </div>
);

export const CardBody = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6", className)} {...props}>
    {children}
  </div>
);

export const CardFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-t border-slate-100", className)} {...props}>
    {children}
  </div>
);
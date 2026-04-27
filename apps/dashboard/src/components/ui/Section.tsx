import React from "react";
import { cn } from "@/lib/utils";

export interface SectionProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "hero" | "featured" | "compact";
  withBackground?: boolean;
  withPattern?: boolean;
  className?: string;
}

export const Section = React.forwardRef<HTMLDivElement, SectionProps>(
  ({ className, variant = "default", withBackground = false, withPattern = false, children, ...props }, ref) => {
    const baseStyles = "relative w-full";
    
    const variants = {
      default: "py-16 lg:py-24",
      hero: "py-20 lg:py-32",
      featured: "py-12 lg:py-20 bg-gradient-to-b from-transparent via-cyan-400/5 to-transparent",
      compact: "py-8 lg:py-12",
    };

    return (
      <section
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          withBackground && "bg-black/40",
          withPattern && "cyber-grid opacity-10",
          className
        )}
        {...props}
      >
        {withPattern && (
          <>
            <div className="absolute inset-0 noise-overlay pointer-events-none" />
            <div className="absolute inset-0 scanline opacity-10 pointer-events-none" />
          </>
        )}
        <div className="relative z-10">
          {children}
        </div>
      </section>
    );
  }
);

Section.displayName = "Section";

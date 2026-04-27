import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export interface BaseLayoutProps {
  children: React.ReactNode;
  variant?: "landing" | "auth" | "dashboard";
  withBackground?: boolean;
  withPattern?: boolean;
  className?: string;
  containerClassName?: string;
}

export const BaseLayout = React.forwardRef<HTMLDivElement, BaseLayoutProps>(
  ({ 
    children, 
    variant = "dashboard", 
    withBackground = true, 
    withPattern = false,
    className = "",
    containerClassName = "",
  }, ref) => {
    
    const variantStyles = {
      landing: "min-h-screen bg-slate-50 text-slate-900",
      auth: "min-h-screen bg-slate-50 text-slate-900 flex items-center justify-center p-6",
      dashboard: "min-h-screen bg-slate-50 text-slate-900 relative overflow-hidden",
    };

    const backgroundStyles = withBackground ? "relative" : "";

    return (
      <div
        ref={ref}
        className={cn(
          variantStyles[variant],
          backgroundStyles,
          className
        )}
      >
        {/* Background Effects - Clean & Subtle */}
        {withBackground && variant !== "auth" && (
          <>
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/50 via-slate-50 to-amber-50/50 pointer-events-none z-0" />
            <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(251, 191, 36, 0.08) 0%, transparent 50%)', pointerEvents: 'none', zIndex: 0 }} />
          </>
        )}

        {/* Content Container */}
        <div className={cn(
          "relative z-10",
          variant === "auth" ? "w-full max-w-md" : "w-full",
          containerClassName
        )}>
          <AnimatePresence mode="wait">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="w-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    );
  }
);

BaseLayout.displayName = "BaseLayout";
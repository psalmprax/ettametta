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
      landing: "min-h-screen bg-black text-white",
      auth: "min-h-screen bg-black text-white flex items-center justify-center p-6",
      dashboard: "min-h-screen bg-bg-base text-white relative overflow-hidden",
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
        {/* Background Effects */}
        {withBackground && variant !== "auth" && (
          <>
            <div className="absolute inset-0 noise-overlay pointer-events-none z-0" />
            <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none z-0" />
            <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-0" />
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

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

/** Module-internal — do not consume from outside. */
interface BaseLayoutProps {
  readonly children: React.ReactNode;
  readonly variant?: "landing" | "auth" | "dashboard";
  readonly withBackground?: boolean;
  readonly withPattern?: boolean;
  readonly className?: string;
  readonly containerClassName?: string;
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
      dashboard: "min-h-screen bg-black text-white relative overflow-hidden",
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
        {/* Background Effects - Dark & Subtle */}
        {withBackground && variant !== "auth" && (
          <>
            <div className="absolute inset-0 bg-black pointer-events-none z-0" />
            <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(37, 99, 235, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(37, 99, 235, 0.03) 0%, transparent 50%)', pointerEvents: 'none', zIndex: 0 }} />
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
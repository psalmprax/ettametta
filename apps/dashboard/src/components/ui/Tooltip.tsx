"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface TooltipProps {
    readonly content: string;
    readonly children: React.ReactNode;
    readonly position?: "top" | "bottom" | "left" | "right";
    readonly delay?: number;
}

export const Tooltip: React.FC<TooltipProps> = ({
    content,
    children,
    position = "top",
    delay = 400,
}) => {
    const [isVisible, setIsVisible] = useState(false);
    const [shouldShow, setShouldShow] = useState(false);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const tooltipRef = useRef<HTMLDivElement>(null);

    const positionStyles: Record<string, string> = {
        top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
        bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
        left: "right-full top-1/2 -translate-y-1/2 mr-2",
        right: "left-full top-1/2 -translate-y-1/2 ml-2",
    };

    const arrowStyles: Record<string, string> = {
        top: "top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-zinc-800",
        bottom: "bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-zinc-800",
        left: "left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-zinc-800",
        right: "right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-zinc-800",
    };

    useEffect(() => {
        return () => {
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, []);

    const handleMouseEnter = () => {
        setShouldShow(true);
        timeoutRef.current = setTimeout(() => {
            setIsVisible(true);
        }, delay);
    };

    const handleMouseLeave = () => {
        setShouldShow(false);
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setIsVisible(false);
    };

    return (
        <div
            className="relative inline-block"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onFocus={handleMouseEnter}
            onBlur={handleMouseLeave}
        >
            {children}
            <AnimatePresence>
                {isVisible && shouldShow && (
                    <motion.div
                        ref={tooltipRef}
                        initial={{ opacity: 0, scale: 0.95, y: position === "top" ? 4 : position === "bottom" ? -4 : 0 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: position === "top" ? 4 : position === "bottom" ? -4 : 0 }}
                        transition={{ duration: 0.15, ease: "easeOut" }}
                        className={cn(
                            "absolute z-50 px-3 py-2 rounded-xl bg-zinc-800 border border-white/10 text-[10px] font-medium text-zinc-200 whitespace-normal max-w-[220px] text-center leading-relaxed shadow-xl pointer-events-none",
                            positionStyles[position]
                        )}
                        role="tooltip"
                    >
                        {content}
                        <div
                            className={cn(
                                "absolute w-0 h-0 border-4",
                                arrowStyles[position]
                            )}
                        />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

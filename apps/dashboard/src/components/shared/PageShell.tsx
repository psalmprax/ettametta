"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";

/** Module-internal — do not consume from outside. */
interface PageShellProps {
    readonly activeKey: string;
    readonly children: React.ReactNode;
}

/**
 * Shared animated page shell for CommandCenterLayout-based pages.
 * Wraps content with AnimatePresence + motion.div transitions.
 * Replaces the identical transition pattern in 6+ dashboard pages.
 */
export function PageShell({ activeKey, children }: PageShellProps) {
    return (
        <div className="p-10 space-y-10 relative h-full flex flex-col">
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeKey}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="flex-1 flex flex-col min-h-0"
                >
                    {children}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}

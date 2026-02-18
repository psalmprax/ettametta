"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface SkeletonProps {
    className?: string;
    variant?: "default" | "card" | "text" | "circle";
}

export function Skeleton({ className, variant = "default" }: SkeletonProps) {
    const variants = {
        default: "rounded-md",
        card: "rounded-[2rem]",
        text: "rounded-full h-4",
        circle: "rounded-full"
    };

    return (
        <div className={cn(
            "relative overflow-hidden bg-white/5",
            variants[variant],
            className
        )}>
            <motion.div
                initial={{ x: "-100%" }}
                animate={{ x: "100%" }}
                transition={{
                    repeat: Infinity,
                    duration: 2,
                    ease: "linear",
                }}
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent"
            />
        </div>
    );
}

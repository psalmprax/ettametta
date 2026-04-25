"use client";

import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    description: string;
    confirmText?: string;
    cancelText?: string;
    variant?: "danger" | "primary" | "success";
    isLoading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    description,
    confirmText = "Confirm",
    cancelText = "Cancel",
    variant = "danger",
    isLoading = false
}) => {
    const previousActiveElement = useRef<HTMLElement | null>(null);

    // Handle escape key and focus management
    useEffect(() => {
        if (isOpen) {
            previousActiveElement.current = document.activeElement as HTMLElement;

            // Focus cancel button after modal opens
            const timer = setTimeout(() => {
                const cancelBtn = document.querySelector('[data-modal-cancel]');
                if (cancelBtn) (cancelBtn as HTMLElement).focus();
            }, 100);

            const handleEscape = (e: KeyboardEvent) => {
                if (e.key === 'Escape') onClose();
            };
            document.addEventListener('keydown', handleEscape);

            return () => {
                clearTimeout(timer);
                document.removeEventListener('keydown', handleEscape);
            };
        } else {
            // Restore focus when modal closes
            if (previousActiveElement.current) {
                previousActiveElement.current.focus();
            }
        }
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center p-6"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="confirm-modal-title"
                >
                    <div 
                        className="absolute inset-0 bg-black/80 backdrop-blur-xl transition-all" 
                        onClick={onClose}
                        aria-hidden="true"
                    />

                    <motion.div
                        initial={{ scale: 0.95, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.95, opacity: 0, y: 20 }}
                        className="relative w-full max-w-lg glass-card p-10 space-y-8 overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)] border-white/10"
                    >
                        <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                        
                        <div className="flex flex-col items-center text-center space-y-6 relative z-10">
                            <div className={cn(
                                "h-20 w-20 rounded-3xl flex items-center justify-center border transition-all duration-500",
                                variant === "danger" ? "bg-red-500/10 border-red-500/30 text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.2)]" :
                                variant === "success" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.2)]" :
                                "bg-primary/10 border-primary/30 text-primary shadow-[0_0_30px_rgba(var(--primary-rgb),0.2)]"
                            )}>
                                {variant === "danger" ? <AlertTriangle className="h-10 w-10 animate-pulse" /> : 
                                 variant === "success" ? <CheckCircle2 className="h-10 w-10" /> : 
                                 <AlertTriangle className="h-10 w-10" />}
                            </div>

                            <div className="space-y-2">
                                <h3 id="confirm-modal-title" className="text-3xl font-black text-white uppercase tracking-tighter">
                                    {title}
                                </h3>
                                <p className="text-zinc-500 font-medium text-sm leading-relaxed max-w-xs mx-auto">
                                    {description}
                                </p>
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-4 relative z-10">
                            <button
                                data-modal-cancel
                                onClick={onClose}
                                disabled={isLoading}
                                className="flex-1 py-4 rounded-2xl bg-zinc-900 border border-white/5 text-zinc-500 font-black uppercase text-[10px] tracking-widest hover:text-white hover:bg-zinc-800 transition-all disabled:opacity-50"
                            >
                                {cancelText}
                            </button>
                            <button
                                onClick={onConfirm}
                                disabled={isLoading}
                                className={cn(
                                    "flex-1 py-4 rounded-2xl font-black uppercase text-[10px] tracking-widest transition-all shadow-lg hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50",
                                    variant === "danger" ? "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20" :
                                    variant === "success" ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/20" :
                                    "bg-primary hover:bg-primary/90 text-white shadow-primary/20"
                                )}
                            >
                                {isLoading ? "Processing..." : confirmText}
                            </button>
                        </div>

                        <button
                            onClick={onClose}
                            className="absolute top-6 right-6 p-2 rounded-xl bg-white/5 border border-white/10 text-zinc-500 hover:text-white transition-all z-20"
                            aria-label="Close modal"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

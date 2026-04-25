"use client";

import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { COLORS, RADIUS } from '@/lib/theme';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ label, error, leftIcon, rightIcon, className, ...props }, ref) => {
        return (
            <div className="w-full space-y-2">
                {label && (
                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">
                        {label}
                    </label>
                )}
                <div className="relative group">
                    {leftIcon && (
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600 group-focus-within:text-primary transition-colors">
                            {leftIcon}
                        </div>
                    )}
                    <input
                        ref={ref}
                        className={cn(
                            'w-full bg-zinc-950/50 border rounded-xl py-4 px-4 transition-all',
                            'focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary',
                            'placeholder:text-zinc-700 text-white font-medium',
                            leftIcon && 'pl-12',
                            rightIcon && 'pr-12',
                            error
                                ? 'border-red-500/20 focus:border-red-500 focus:ring-red-500/40'
                                : 'border-white/10 hover:border-white/20',
                            className
                        )}
                        {...props}
                    />
                    {rightIcon && (
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-600 group-focus-within:text-primary transition-colors">
                            {rightIcon}
                        </div>
                    )}
                </div>
                {error && (
                    <p className="text-xs text-red-500 font-medium">{error}</p>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';

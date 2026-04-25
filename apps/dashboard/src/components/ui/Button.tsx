"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
}

export function Button({
    children,
    variant = 'primary',
    size = 'md',
    isLoading = false,
    leftIcon,
    rightIcon,
    className,
    disabled,
    ...props
}: ButtonProps) {
    const baseStyles = `
        inline-flex items-center justify-center gap-2 font-black uppercase tracking-widest
        transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-current
        rounded-xl
    `;

    const variants = {
        primary: `
            bg-primary hover:bg-primary/90 text-white
            shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]
            hover:shadow-[0_0_40px_rgba(var(--primary-rgb),0.3)]
            focus-visible:ring-primary/50
        `,
        secondary: `
            bg-white/5 hover:bg-white/10 text-zinc-400
            border border-white/10 hover:border-white/20
            focus-visible:ring-white/20
        `,
        ghost: `
            bg-transparent hover:bg-white/5 text-zinc-400
            hover:text-white
            focus-visible:ring-white/20
        `,
        danger: `
            bg-red-500 hover:bg-red-600 text-white
            shadow-[0_0_20px_rgba(239,68,68,0.3)]
            hover:shadow-[0_0_30px_rgba(239,68,68,0.4)]
            focus-visible:ring-red-500/50
        `,
        success: `
            bg-emerald-500 hover:bg-emerald-600 text-white
            shadow-[0_0_20px_rgba(16,185,129,0.2)]
            hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]
            focus-visible:ring-emerald-500/50
        `,
    };

    const sizes = {
        sm: 'px-3 py-2 text-[10px]',
        md: 'px-5 py-3 text-sm',
        lg: 'px-8 py-4 text-base',
    };

    return (
        <button
            className={cn(
                baseStyles,
                variants[variant],
                sizes[size],
                className
            )}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
            ) : leftIcon ? (
                <span className="h-4 w-4">{leftIcon}</span>
            ) : null}
            {children}
            {rightIcon && <span className="h-4 w-4">{rightIcon}</span>}
        </button>
    );
}


export function Button({
    children,
    variant = 'primary',
    size = 'md',
    isLoading = false,
    leftIcon,
    rightIcon,
    className,
    disabled,
    ...props
}: ButtonProps) {
    const baseStyles = `
        inline-flex items-center justify-center gap-2 font-black uppercase tracking-widest
        transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-current
        rounded-xl
    `;

    const variants = {
        primary: `
            bg-primary hover:bg-primary/90 text-white
            shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]
            hover:shadow-[0_0_40px_rgba(var(--primary-rgb),0.3)]
            focus-visible:ring-primary/50
        `,
        secondary: `
            bg-white/5 hover:bg-white/10 text-zinc-400
            border border-white/10 hover:border-white/20
            focus-visible:ring-white/20
        `,
        ghost: `
            bg-transparent hover:bg-white/5 text-zinc-400
            hover:text-white
            focus-visible:ring-white/20
        `,
        danger: `
            bg-red-500 hover:bg-red-600 text-white
            shadow-[0_0_20px_rgba(239,68,68,0.3)]
            hover:shadow-[0_0_30px_rgba(239,68,68,0.4)]
            focus-visible:ring-red-500/50
        `,
        success: `
            bg-emerald-500 hover:bg-emerald-600 text-white
            shadow-[0_0_20px_rgba(16,185,129,0.2)]
            hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]
            focus-visible:ring-emerald-500/50
        `,
    };

    const sizes = {
        sm: 'px-3 py-2 text-[10px]',
        md: 'px-5 py-3 text-sm',
        lg: 'px-8 py-4 text-base',
    };

    return (
        <button
            className={cn(
                baseStyles,
                variants[variant],
                sizes[size],
                className
            )}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
            ) : leftIcon ? (
                <span className="h-4 w-4">{leftIcon}</span>
            ) : null}
            {children}
            {rightIcon && <span className="h-4 w-4">{rightIcon}</span>}
        </button>
    );
}

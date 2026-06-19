// fallow-ignore-file unused-export
/**
 * Design System Tokens for Ettametta
 * Centralized source of truth for visual styling.
 * Based on Tailwind utility values with semantic naming.
 */

export const COLORS = {
    // Brand
    primary: 'var(--primary)',
    primaryRGB: 'var(--primary-rgb)',
    primaryHover: 'var(--primary-hover, rgba(var(--primary-rgb), 0.9))',
    
    // Semantic
    success: '#10b981',      // emerald-500
    successLight: 'rgba(16, 185, 129, 0.1)',
    successBorder: 'rgba(16, 185, 129, 0.2)',
    warning: '#f59e0b',      // amber-500
    warningLight: 'rgba(245, 158, 11, 0.1)',
    warningBorder: 'rgba(245, 158, 11, 0.2)',
    danger: '#ef4444',       // red-500
    dangerLight: 'rgba(239, 68, 68, 0.1)',
    dangerBorder: 'rgba(239, 68, 68, 0.2)',
    info: '#06b6d4',         // cyan-400
    infoLight: 'rgba(6, 182, 212, 0.1)',
    infoBorder: 'rgba(6, 182, 212, 0.2)',
    
    // Neutrals (zinc palette)
    white: '#ffffff',
    zinc900: '#18181b',   // zinc-900
    zinc950: '#09090b',   // zinc-950
    zinc800: '#27272a',   // zinc-800
    zinc700: '#3f3f46',   // zinc-700
    zinc600: '#52525b',   // zinc-600
    zinc500: '#71717a',   // zinc-500
    zinc400: '#a1a1aa',   // zinc-400
    zinc300: '#d4d4d8',   // zinc-300
    
    // Additional accents
    violet: '#8b5cf6',    // violet-500
    violetLight: 'rgba(139, 92, 246, 0.1)',
    cyan: '#22d3ee',      // cyan-400
    emerald: '#10b981',   // emerald-500
    rose: '#f43f5e',      // rose-500
} as const;

export const SPACING = {
    0: '0',
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
    16: '4rem',     // 64px
    20: '5rem',     // 80px
} as const;

export const RADIUS = {
    none: '0',
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    '2xl': '1.5rem',
    '3xl': '2rem',
    '4xl': '3rem',
    '5xl': '4rem',
    full: '9999px',
} as const;

export const FONT_SIZE = {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
    '5xl': '3rem',     // 48px
    '6xl': '3.75rem',  // 60px
    '7xl': '4.5rem',   // 72px
} as const;

export const FONT_WEIGHT = {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    black: '900',
} as const;

export const Z_INDEX = {
    auto: 'auto',
    0: '0',
    10: '10',
    20: '20',
    30: '30',
    40: '40',
    50: '50',
    100: '100',
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
    notification: 1080,
} as const;

export const SHADOWS = {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    glowPrimary: '0 0 20px rgba(var(--primary-rgb), 0.3)',
    glowPrimaryLarge: '0 0 40px rgba(var(--primary-rgb), 0.3)',
    glowViolet: '0 0 20px rgba(139, 92, 246, 0.3)',
    glowVioletLarge: '0 0 40px rgba(139, 92, 246, 0.3)',
    glowCyan: '0 0 20px rgba(34, 211, 238, 0.3)',
    glowCyanLarge: '0 0 40px rgba(34, 211, 238, 0.3)',
    glowEmerald: '0 0 20px rgba(16, 185, 129, 0.2)',
    glowEmeraldLarge: '0 0 40px rgba(16, 185, 129, 0.2)',
    glowRose: '0 0 20px rgba(244, 63, 94, 0.3)',
} as const;

export const TRANSITION = {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
    slower: '500ms',
} as const;

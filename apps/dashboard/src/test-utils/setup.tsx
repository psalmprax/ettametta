import '@testing-library/jest-dom/vitest';
import React from 'react';
import { vi, beforeEach } from 'vitest';

// Default search params; override per-test via setSearchParams() mock below.
const DEFAULT_PARAMS = new URLSearchParams();

// next/navigation: mock useSearchParams, useRouter, usePathname stable across tests.
vi.mock('next/navigation', () => {
    const params = new URLSearchParams();
    return {
        useSearchParams: () => params,
        useRouter: () => ({
            push: vi.fn(),
            replace: vi.fn(),
            refresh: vi.fn(),
            back: vi.fn(),
            forward: vi.fn(),
            prefetch: vi.fn(),
        }),
        usePathname: () => '/nexus',
        useParams: () => ({}),
    };
});

// sonner: silence toasts so they don't leak render warnings in tests.
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
        info: vi.fn(),
        warning: vi.fn(),
        promise: vi.fn((p: Promise<unknown>) => p),
    },
}));

// next/link: render as plain <a> in tests.
vi.mock('next/link', () => ({
    default: ({ children, href, ...rest }: any) => (
        <a href={typeof href === 'string' ? href : '#'} {...rest}>
            {children}
        </a>
    ),
}));

// framer-motion: drop motion wrappers to plain DOM nodes (avoids layout/animation side-effects in tests).
vi.mock('framer-motion', () => ({
    motion: new Proxy(
        {},
        {
            get: (_t, prop: string) => {
                return ({ children, ...rest }: any) => {
                    const Tag = prop as keyof JSX.IntrinsicElements;
                    return (
                        // @ts-expect-error - dynamic tag
                        <Tag {...rest}>{children}</Tag>
                    );
                };
            },
        },
    ),
    AnimatePresence: ({ children }: any) => children,
    useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
    useMotionValue: (init: number) => ({ current: init }),
    useTransform: () => ({ current: 0 }),
    useSpring: () => ({ current: 0 }),
}));

// Reset between tests to keep state isolated.
beforeEach(() => {
    vi.clearAllMocks();
    if (typeof window !== 'undefined') {
        window.localStorage.clear();
        window.sessionStorage.clear();
    }
});

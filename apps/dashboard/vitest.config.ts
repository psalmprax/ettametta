import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
    test: {
        environment: 'happy-dom',
        globals: true,
        setupFiles: ['./src/test-utils/setup.tsx'],
        include: ['src/**/__tests__/**/*.{test,spec}.{ts,tsx}'],
        css: false,
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
});

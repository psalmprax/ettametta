import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "on-secondary": "#520070",
                "surface-container": "#201f1f",
                "on-error-container": "#ffdad6",
                "tertiary": "#ffffff",
                "secondary-container": "#d05bff",
                "on-background": "#e5e2e1",
                "surface-variant": "#353534",
                "on-secondary-fixed-variant": "#75009e",
                "outline-variant": "#3a4a49",
                "tertiary-fixed-dim": "#2ae500",
                "error-container": "#93000a",
                "surface-dim": "#131313",
                "on-primary-fixed-variant": "#004f4f",
                "surface": "#131313",
                "primary-container": "#00fbfb",
                "on-tertiary": "#053900",
                "surface-container-lowest": "#0e0e0e",
                "surface-container-low": "#1c1b1b",
                "on-tertiary-fixed": "#022100",
                "inverse-surface": "#e5e2e1",
                "on-secondary-container": "#480063",
                "on-primary-container": "#007070",
                "on-error": "#690005",
                "tertiary-fixed": "#79ff5b",
                "primary-fixed-dim": "#00dddd",
                "on-tertiary-container": "#117500",
                "inverse-on-surface": "#313030",
                "tertiary-container": "#79ff5b",
                "primary-fixed": "#00fbfb",
                "primary": "#ffffff",
                "surface-tint": "#00dddd",
                "error": "#ffb4ab",
                "on-primary": "#003737",
                "surface-container-high": "#2a2a2a",
                "on-surface": "#e5e2e1",
                "secondary-fixed-dim": "#ecb1ff",
                "secondary": "#ecb1ff",
                "on-secondary-fixed": "#320046",
                "surface-bright": "#393939",
                "on-primary-fixed": "#002020",
                "secondary-fixed": "#f9d8ff",
                "surface-container-highest": "#353534",
                "on-surface-variant": "#b9cac9",
                "background": "#131313",
                "inverse-primary": "#006a6a",
                "outline": "#839493",
                "on-tertiary-fixed-variant": "#095300",

                // Previous colors preserved
                "neon-violet": "#8b5cf6",
                "neon-cyan": "#22d3ee",
                "brand-dark": "#0a0a0f",
                "cyan-glow": "#00e0ff",
                "emerald-accent": "#00ff7f",
            },
            borderRadius: {
                DEFAULT: "0.125rem",
                "sm": "0.125rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "xl": "0.75rem",
                "2xl": "1rem",
                "3xl": "1.5rem",
                "4xl": "2rem",
                "full": "9999px"
            },
            spacing: {
                "container-margin": "20px",
                "gutter": "12px",
                "unit": "4px",
                "xs": "4px",
                "xl": "40px",
                "md": "16px",
                "lg": "24px",
                "sm": "8px"
            },
            fontFamily: {
                "space-grotesk": ["Space Grotesk", "sans-serif"],
                "data-mono": ["Space Grotesk", "sans-serif"],
                "label-caps": ["Space Grotesk", "sans-serif"],
                "display-lg": ["Space Grotesk", "sans-serif"],
                "headline-md": ["Space Grotesk", "sans-serif"],
                "body-base": ["Inter", "sans-serif"]
            },
            fontSize: {
                "data-mono": ["14px", {"lineHeight": "1.4", "letterSpacing": "0.05em", "fontWeight": "500"}],
                "label-caps": ["12px", {"lineHeight": "1.2", "fontWeight": "700"}],
                "display-lg": ["40px", {"lineHeight": "1.1", "letterSpacing": "-0.02em", "fontWeight": "700"}],
                "headline-md": ["24px", {"lineHeight": "1.2", "fontWeight": "600"}],
                "body-base": ["16px", {"lineHeight": "1.5", "fontWeight": "400"}]
            },
            boxShadow: {
                "glow-violet": "0 0 20px rgba(139, 92, 246, 0.3), 0 0 40px rgba(139, 92, 246, 0.1)",
                "glow-cyan": "0 0 20px rgba(34, 211, 238, 0.3), 0 0 40px rgba(34, 211, 238, 0.1)",
                "inner-glow": "inset 0 1px 1px rgba(255, 255, 255, 0.05)",
            },
            animation: {
                "spin-slow": "spin 3s linear infinite",
                "pulse-neon": "pulse-neon 4s ease-in-out infinite",
                "float": "float 6s ease-in-out infinite",
            },
            keyframes: {
                "pulse-neon": {
                    "0%, 100%": { opacity: "1", filter: "brightness(1)" },
                    "50%": { opacity: "0.8", filter: "brightness(1.5)" },
                },
                "float": {
                    "0%, 100%": { transform: "translateY(0px)" },
                    "50%": { transform: "translateY(-10px)" },
                },
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/container-queries')
    ],
};
export default config;

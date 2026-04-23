"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

type UITheme = "legacy" | "modern";

interface UIThemeContextType {
    theme: UITheme;
    setTheme: (theme: UITheme) => void;
    toggleTheme: () => void;
}

const UIThemeContext = createContext<UIThemeContextType>({
    theme: "legacy",
    setTheme: () => {},
    toggleTheme: () => {},
});

const THEME_KEY = "ettametta_ui_theme";

export function UIThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setThemeState] = useState<UITheme>("legacy");
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const saved = localStorage.getItem(THEME_KEY) as UITheme;
        if (saved) {
            setThemeState(saved);
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            const urlTheme = urlParams.get("ui_theme") as UITheme;
            if (urlTheme === "modern") {
                setThemeState("modern");
            }
        }
    }, []);

    const setTheme = (newTheme: UITheme) => {
        setThemeState(newTheme);
        localStorage.setItem(THEME_KEY, newTheme);
    };

    const toggleTheme = () => {
        setTheme(theme === "legacy" ? "modern" : "legacy");
    };

    if (!mounted) {
        return <>{children}</>;
    }

    return (
        <UIThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
            {children}
        </UIThemeContext.Provider>
    );
}

export function useUITheme() {
    return useContext(UIThemeContext);
}

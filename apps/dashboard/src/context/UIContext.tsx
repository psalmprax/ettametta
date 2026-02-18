"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

interface UIContextType {
    isProMode: boolean;
    toggleProMode: () => void;
}

const UIContext = createContext<UIContextType | undefined>(undefined);

export function UIProvider({ children }: { children: React.ReactNode }) {
    const [isProMode, setIsProMode] = useState(false);

    // Initial load from localStorage
    useEffect(() => {
        const saved = localStorage.getItem("vf_pro_mode");
        if (saved === "true") setIsProMode(true);
    }, []);

    const toggleProMode = () => {
        setIsProMode(prev => {
            const next = !prev;
            localStorage.setItem("vf_pro_mode", String(next));
            return next;
        });
    };

    return (
        <UIContext.Provider value={{ isProMode, toggleProMode }}>
            <div className={isProMode ? "pro-mode" : ""}>
                {children}
            </div>
        </UIContext.Provider>
    );
}

export function useUI() {
    const context = useContext(UIContext);
    if (context === undefined) {
        throw new Error("useUI must be used within a UIProvider");
    }
    return context;
}

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
        const saved = localStorage.getItem("et_pro_mode");
        if (saved === "true") {
            setIsProMode(true);
        } else {
            // Migrate from old vf_pro_mode key
            const legacy = localStorage.getItem("vf_pro_mode");
            if (legacy === "true") {
                setIsProMode(true);
                localStorage.setItem("et_pro_mode", "true");
                localStorage.removeItem("vf_pro_mode");
            }
        }
    }, []);

    const toggleProMode = () => {
        setIsProMode(prev => {
            const next = !prev;
            localStorage.setItem("et_pro_mode", String(next));
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

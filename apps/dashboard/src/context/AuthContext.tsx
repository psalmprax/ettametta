"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
    username: string;
    email: string;
    role: string;
    subscription: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (token: string) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    const publicPaths = ["/login", "/register"];

    const logout = () => {
        localStorage.removeItem("vf_token");
        setToken(null);
        setUser(null);
        router.push("/login");
    };

    const fetchUser = async (authToken: string) => {
        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${authToken}` },
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else if (response.status === 401) {
                console.warn("Session expired or invalid token. Logging out.");
                logout();
            } else {
                console.error("Failed to fetch user, status:", response.status);
                // Optionally logout on other critical errors if needed
            }
        } catch (err) {
            console.error("Failed to fetch user:", err);
            // Don't logout on network error, keep current state
        } finally {
            setIsLoading(false);
        }
    };

    const login = (newToken: string) => {
        localStorage.setItem("vf_token", newToken);
        setToken(newToken);
        fetchUser(newToken);
    };

    useEffect(() => {
        const storedToken = localStorage.getItem("vf_token");
        if (storedToken) {
            setToken(storedToken);
            fetchUser(storedToken);
        } else {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        if (!isLoading) {
            const isPublicPath = publicPaths.includes(pathname);
            if (!token && !isPublicPath) {
                router.push("/login");
            } else if (token && isPublicPath) {
                router.push("/");
            }
        }
    }, [token, isLoading, pathname]);

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

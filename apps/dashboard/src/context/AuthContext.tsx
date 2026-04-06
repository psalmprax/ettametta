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
    login: (token: string, remember?: boolean) => void;
    logout: () => void;
}

// Secure token management
class TokenManager {
    private static readonly TOKEN_KEY = "et_token";
    private static readonly USER_KEY = "et_user";

    static setToken(token: string, remember: boolean = false): void {
        const storage = remember ? localStorage : sessionStorage;
        storage.setItem(this.TOKEN_KEY, token);
    }

    static getToken(): string | null {
        // Check sessionStorage first (preferred for security)
        let token = sessionStorage.getItem(this.TOKEN_KEY);
        if (!token) {
            // Fallback to localStorage for backward compatibility
            token = localStorage.getItem(this.TOKEN_KEY);
        }
        return token;
    }

    static clearToken(): void {
        localStorage.removeItem(this.TOKEN_KEY);
        sessionStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    }

    static setUser(user: User): void {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }

    static getUser(): User | null {
        try {
            const userStr = localStorage.getItem(this.USER_KEY);
            return userStr ? JSON.parse(userStr) : null;
        } catch {
            return null;
        }
    }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

import { API_BASE } from "@/lib/config";
import { withRealFallback } from "@/lib/real_first_utils";

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    const publicPaths = ["/login", "/register"];

    const logout = () => {
        TokenManager.clearToken();
        setToken(null);
        setUser(null);
        router.push("/login");
    };

    const login = (authToken: string, remember: boolean = false) => {
        TokenManager.setToken(authToken, remember);
        setToken(authToken);
    };

    const fetchUser = async (authToken: string) => {
        await withRealFallback(
            async () => {
                return fetch(`${API_BASE}/auth/me`, {
                    headers: { Authorization: `Bearer ${authToken}` },
                });
            },
            {
                fallback: null,
            }
        ).then(async (response) => {
            if (response && response.ok) {
                const userData = await response.json();
                setUser(userData);
                TokenManager.setUser(userData);
            } else {
                // Invalid token, logout
                logout();
            }
        }).catch((error) => {
            console.error("Failed to fetch user:", error);
            logout();
        });
    };

    useEffect(() => {
        const initAuth = async () => {
            const storedToken = TokenManager.getToken();
            const storedUser = TokenManager.getUser();

            if (storedToken) {
                setToken(storedToken);
                if (storedUser) {
                    setUser(storedUser);
                } else {
                    await fetchUser(storedToken);
                }
            }

            setIsLoading(false);
        };

        initAuth();
    }, []);

    useEffect(() => {
        if (!isLoading && !user && !publicPaths.includes(pathname)) {
            router.push("/login");
        }
    }, [user, isLoading, pathname, router]);

    return {
        user,
        token,
        isLoading,
        login,
        logout,
    };
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
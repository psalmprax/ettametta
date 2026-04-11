"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
    username: string;
    email: string;
    role: string;
    subscription: string;
    telegram_chat_id?: string;
    telegram_token?: string;
    whatsapp_number?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    credits: number | null;
    isLoading: boolean;
    login: (token: string, remember?: boolean) => void;
    logout: () => void;
    refreshCredits: () => Promise<void>;
}

// Secure token management
class TokenManager {
    private static readonly TOKEN_KEY = "et_token";
    private static readonly USER_KEY = "et_user";
    private static readonly CREDITS_KEY = "et_credits";

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
        localStorage.removeItem(this.CREDITS_KEY);
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

    static setCredits(credits: number): void {
        localStorage.setItem(this.CREDITS_KEY, credits.toString());
    }

    static getCredits(): number | null {
        const credits = localStorage.getItem(this.CREDITS_KEY);
        return credits ? parseInt(credits) : null;
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
                onSuccess: (userData: any) => {
                    if (userData && userData.username) {
                        setUser(userData);
                        TokenManager.setUser(userData);
                    } else {
                        logout();
                    }
                },
                onFallback: () => {
                    logout();
                }
            }
        );
    };

    const [credits, setCredits] = useState<number | null>(null);

    const fetchCredits = async (authToken: string) => {
        await withRealFallback(
            async () => {
                return fetch(`${API_BASE}/credits/balance`, {
                    headers: { Authorization: `Bearer ${authToken}` },
                });
            },
            {
                fallback: null,
                onSuccess: (data: any) => {
                    if (data && typeof data.balance === "number") {
                        setCredits(data.balance);
                        TokenManager.setCredits(data.balance);
                    }
                }
            }
        );
    };

    const initAuth = async () => {
        const storedToken = TokenManager.getToken();
        const storedUser = TokenManager.getUser();
        const storedCredits = TokenManager.getCredits();

        if (storedToken) {
            setToken(storedToken);
            if (storedUser) {
                setUser(storedUser);
            }
            if (storedCredits !== null) {
                setCredits(storedCredits);
            }
            // Always fetch fresh user and credits if we have a token
            await Promise.all([
                fetchUser(storedToken),
                fetchCredits(storedToken)
            ]);
        }

        setIsLoading(false);
    };

    useEffect(() => {
        initAuth();
    }, []);

    const refreshCredits = async () => {
        if (token) {
            await fetchCredits(token);
        }
    };

    useEffect(() => {
        if (!isLoading && !user && !publicPaths.includes(pathname)) {
            router.push("/login");
        }
    }, [user, isLoading, pathname, router]);

    // Periodically refresh credits (every 2 mins)
    useEffect(() => {
        if (token && !isLoading) {
            const interval = setInterval(refreshCredits, 120000);
            return () => clearInterval(interval);
        }
    }, [token, isLoading]);

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isLoading,
                credits,
                login,
                logout,
                refreshCredits,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
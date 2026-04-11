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
    login: (token: string, remember?: boolean) => Promise<boolean>;
    logout: () => void;
    refreshCredits: () => Promise<void>;
}

// Secure token management
class TokenManager {
    private static readonly TOKEN_KEY = "et_token";
    private static readonly USER_KEY = "et_user";
    private static readonly CREDITS_KEY = "et_credits";

    static setToken(token: string, remember: boolean = false): void {
        // Hotfix: Always use localStorage for production stability since many pages 
        // directly reach into localStorage bypass-ing the context.
        localStorage.setItem(this.TOKEN_KEY, token);
        sessionStorage.setItem(this.TOKEN_KEY, token);
    }

    static getToken(): string | null {
        // Check sessionStorage first
        let token = sessionStorage.getItem(this.TOKEN_KEY);
        if (!token) {
            token = localStorage.getItem(this.TOKEN_KEY);
        } else {
            // Sync to localStorage to satisfy direct access from sub-pages
            localStorage.setItem(this.TOKEN_KEY, token);
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

    const login = async (authToken: string, remember: boolean = false) => {
        TokenManager.setToken(authToken, remember);
        setToken(authToken);
        
        // Directly verify token is valid and fetch user WITH proper error handling
        try {
            const userRes = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${authToken}` },
            });
            
            if (!userRes.ok) {
                logout();
                throw new Error("Invalid token received");
            }
            
            const userData = await userRes.json();
            setUser(userData);
            TokenManager.setUser(userData);
            
            // Fetch credits in background, don't block login
            fetchCredits(authToken);
            
            // Explicitly confirm user is loaded before returning
            return true;
        } catch (e) {
            logout();
            throw e;
        }
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

        // Fix "null" string token bug - reject invalid token values
        if (storedToken && storedToken !== "null" && storedToken !== "undefined" && storedToken.trim().length > 0) {
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
        // Never redirect during active login flow - give time for state to propagate
        if (token && !user) return;
        
        // Only redirect after auth initialization is complete AND we have confirmed no user exists
        if (!isLoading && !user && !publicPaths.includes(pathname)) {
            // Always verify both token AND user exist in storage before redirecting
            const storedToken = TokenManager.getToken();
            const storedUser = TokenManager.getUser();
            
            // Only redirect if there is truly no active session at all
            if (!storedToken || !storedUser) {
                router.push("/login");
            }
        }
    }, [user, isLoading, pathname, router, token]);

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
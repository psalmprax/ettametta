"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User } from "@/lib/types";

/** Module-internal — do not consume from outside. */
interface AuthContextType {
    user: User | null;
    token: string | null;
    credits: number | null;
    isLoading: boolean;
    login: (token: string, remember?: boolean) => Promise<boolean>;
    register: (email: string, password: string, username?: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
    refreshCredits: () => Promise<void>;
}

// Secure token management
class TokenManager {
    private static readonly TOKEN_KEY = "et_token";
    private static readonly USER_KEY = "et_user";
    private static readonly CREDITS_KEY = "et_credits";

    static setToken(token: string, remember: boolean = false): void {
        if (!token || token === "undefined" || token === "null") return;
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
        if (token === "null" || token === "undefined") {
            this.clearToken();
            return null;
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

/** Module-internal — do not consume from outside. */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PUBLIC_PATHS = ["/login", "/register"];

import { API_BASE } from "@/lib/config";
import { withRealFallback } from "@/lib/real_first_utils";
import { toast } from "sonner";

export function AuthProvider({ children }: { readonly children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [credits, setCredits] = useState<number | null>(null);
    const router = useRouter();
    const pathname = usePathname();

    const logout = useCallback(() => {
        TokenManager.clearToken();
        setToken(null);
        setUser(null);
        router.push("/login");
    }, [router]);

    const fetchUser = useCallback(async (authToken: string) => {
        await withRealFallback(
            async (signal) => {
                return fetch(`${API_BASE}/auth/me`, {
                    headers: { Authorization: `Bearer ${authToken}` },
                    signal,
                });
            },
            {
                fallback: null as any,
                onUnauthorized: () => {
                    console.warn("[AuthContext] /auth/me returned 401 — logging out");
                    logout();
                },
                onSuccess: (userData: User) => {
                    if (userData && (userData.username || userData.email)) {
                        setUser(userData);
                        TokenManager.setUser(userData);
                    } else {
                        logout();
                    }
                },
                onFallback: (err) => {
                    console.warn("[AuthContext] Failed to refresh user profile, preserving local session:", err);
                }
            }
        );
    }, [logout]);

    const fetchCredits = useCallback(async (authToken: string) => {
        await withRealFallback(
            async (signal) => {
                return fetch(`${API_BASE}/credits/balance`, {
                    headers: { Authorization: `Bearer ${authToken}` },
                    signal,
                });
            },
            {
                fallback: null as any,
                onSuccess: (data: { balance: number }) => {
                    if (data && typeof data.balance === "number") {
                        setCredits(data.balance);
                        TokenManager.setCredits(data.balance);
                    }
                }
            }
        );
    }, []);

    const login = useCallback(async (authToken: string, remember: boolean = false) => {
        if (!authToken || authToken === "undefined" || authToken === "null") {
            console.error("AuthContext: Attempted login with invalid token:", authToken);
            toast.error("Invalid login token — please try logging in again");
            return false;
        }

        TokenManager.setToken(authToken, remember);
        setToken(authToken);
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            const userRes = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${authToken}` },
                signal: controller.signal,
            });
            clearTimeout(timeoutId);
            
            if (!userRes.ok) {
                logout();
                throw new Error("Invalid token received");
            }
            
            const responseData = await userRes.json();
            const userData = responseData?.data || responseData;
            setUser(userData);
            TokenManager.setUser(userData);
            
            fetchCredits(authToken);
            
            return true;
        } catch (e) {
            logout();
            throw e;
        }
    }, [logout, fetchCredits]);

    const register = useCallback(async (email: string, password: string, username?: string) => {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            const response = await fetch(`${API_BASE}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, username }),
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            if (response.ok) {
                return { success: true };
            } else {
                const data = await response.json();
                const errorMessage = data.error?.message || data.message || data.detail || "Registration failed";
                return { success: false, error: errorMessage };
            }
        } catch (err) {
            return { success: false, error: "Connection failed" };
        }
    }, []);

    const initAuth = useCallback(async () => {
        const storedToken = TokenManager.getToken();
        const storedUser = TokenManager.getUser();
        const storedCredits = TokenManager.getCredits();

        if (storedToken && storedToken !== "null" && storedToken !== "undefined" && storedToken.trim().length > 0) {
            setToken(storedToken);
            if (storedUser) {
                setUser(storedUser);
            }
            if (storedCredits !== null) {
                setCredits(storedCredits);
            }
            await Promise.all([
                fetchUser(storedToken),
                fetchCredits(storedToken)
            ]);
        }

        setIsLoading(false);
    }, [fetchUser, fetchCredits]);

    useEffect(() => {
        initAuth();
    }, [initAuth]);

    const refreshCredits = useCallback(async () => {
        if (token) {
            await fetchCredits(token);
        }
    }, [token, fetchCredits]);

    useEffect(() => {
        if (token && !user) return;
        
        if (!isLoading && !user && !PUBLIC_PATHS.includes(pathname)) {
            const storedToken = TokenManager.getToken();
            const storedUser = TokenManager.getUser();
            
            if (!storedToken || !storedUser) {
                router.push("/login");
            }
        }
    }, [user, isLoading, pathname, router, token]);

    useEffect(() => {
        if (token && !isLoading) {
            const interval = setInterval(refreshCredits, 120000);
            return () => clearInterval(interval);
        }
    }, [token, isLoading, refreshCredits]);

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isLoading,
                credits,
                login,
                register,
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

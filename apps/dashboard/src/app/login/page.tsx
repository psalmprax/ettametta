"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, Loader2, Mail, Lock } from "lucide-react";
import Link from "next/link";

import { API_BASE } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";

// Input validation utilities
const validateUsername = (username: string): string | null => {
    if (!username || username.length < 3) {
        return "Username must be at least 3 characters";
    }
    if (username.length > 100) {
        return "Username must be less than 100 characters";
    }
    if (!/^[a-zA-Z0-9_@.-]+$/.test(username)) {
        return "Username can only contain letters, numbers, @, ., and -";
    }
    return null;
};

const validatePassword = (password: string): string | null => {
    if (!password || password.length < 6) {
        return "Password must be at least 6 characters";
    }
    return null;
};

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [remember, setRemember] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [fieldErrors, setFieldErrors] = useState<{username?: string; password?: string}>({});
    const router = useRouter();
    const { login } = useAuth();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");
        setFieldErrors({});

        // Validate inputs
        const usernameError = validateUsername(username);
        const passwordError = validatePassword(password);

        if (usernameError || passwordError) {
            setFieldErrors({
                username: usernameError || undefined,
                password: passwordError || undefined,
            });
            setIsLoading(false);
            return;
        }

        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);

            const response = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                const authToken = data.data?.access_token || data.access_token;
                
                try {
                    // Only proceed if login actually succeeds and user is verified
                    if (!authToken) {
                        throw new Error("No access token found in response");
                    }
                    await login(authToken, remember);
                    // Force a small delay to ensure React state has fully propagated across context boundaries
                    setTimeout(() => {
                        // User is definitely loaded at this point, safe to redirect
                        router.push("/dashboard");
                    }, 50);
                } catch (loginErr) {
                    setError("Session verification failed. Please try again.");
                }
            } else {
                const data = await response.json();
                setError(data.detail || "Invalid credentials");
            }
        } catch (err) {
            setError("Connection failed. Is the API running?");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-6 selection:bg-primary selection:text-black">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center space-y-4">
                    <div className="inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 border border-primary/20 animate-pulse shrink-0">
                        <Zap className="h-10 w-10 text-primary fill-primary" />
                    </div>
                    <h1 className="text-5xl font-black uppercase tracking-tighter text-white">ETTA<span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-emerald-400 text-hollow">METTA</span></h1>
                    <p className="text-zinc-500 font-medium">Log in to your high-velocity workflow</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                        <label htmlFor="username" className="text-xs font-black text-zinc-500 uppercase tracking-widest ml-1">Username</label>
                        <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-600 group-focus-within:text-primary transition-colors" />
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                value={username}
                                onChange={(e) => {
                                    setUsername(e.target.value);
                                    // Clear field error when user starts typing
                                    if (fieldErrors.username) {
                                        setFieldErrors(prev => ({...prev, username: undefined}));
                                    }
                                }}
                                aria-describedby={fieldErrors.username ? "username-error" : undefined}
                                className={`w-full bg-zinc-900 border rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 transition-all text-white font-medium ${
                                    fieldErrors.username
                                        ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500'
                                        : 'border-zinc-800 focus:ring-primary/50 focus:border-primary'
                                }`}
                                placeholder="commander"
                            />
                        </div>
                        {fieldErrors.username && (
                            <p id="username-error" className="text-red-500 text-xs font-medium ml-1">{fieldErrors.username}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="password" className="text-xs font-black text-zinc-500 uppercase tracking-widest ml-1">Password</label>
                        <div className="relative group">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-600 group-focus-within:text-primary transition-colors" />
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => {
                                    setPassword(e.target.value);
                                    // Clear field error when user starts typing
                                    if (fieldErrors.password) {
                                        setFieldErrors(prev => ({...prev, password: undefined}));
                                    }
                                }}
                                aria-describedby={fieldErrors.password ? "password-error" : undefined}
                                className={`w-full bg-zinc-900 border rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 transition-all text-white font-medium ${
                                    fieldErrors.password
                                        ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500'
                                        : 'border-zinc-800 focus:ring-primary/50 focus:border-primary'
                                }`}
                                placeholder="••••••••"
                            />
                        </div>
                        {fieldErrors.password && (
                            <p id="password-error" className="text-red-500 text-xs font-medium ml-1">{fieldErrors.password}</p>
                        )}
                    </div>

                    <div className="flex items-center justify-between">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={remember}
                                onChange={(e) => setRemember(e.target.checked)}
                                className="w-4 h-4 bg-zinc-900 border border-zinc-800 rounded focus:ring-primary focus:ring-2"
                            />
                            <span className="text-zinc-400 text-sm font-medium">Remember me</span>
                        </label>
                    </div>

                    {error && (
                        <div id="login-error" className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm font-bold text-center animate-shake" role="alert" aria-live="assertive">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-white hover:bg-zinc-200 disabled:bg-zinc-800 disabled:text-zinc-500 text-black font-black py-4 rounded-2xl transition-all flex items-center justify-center gap-2 group"
                    >
                        {isLoading ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                            <>
                                AUTHENTICATE
                                <Zap className="h-4 w-4 fill-black group-hover:scale-125 transition-transform" />
                            </>
                        )}
                    </button>
                </form>

                <p className="text-center text-zinc-600 text-sm font-medium">
                    New to Ettametta?{" "}
                    <Link href="/register" className="text-white hover:text-primary transition-colors">
                        Register Access
                    </Link>
                </p>
            </div>
        </div>
    );
}

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, Loader2, Mail, Lock } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { BaseLayout } from "@/components/layout/BaseLayout";

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

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || '/api'}/auth/login`, {
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
        <BaseLayout variant="auth">
            <Card variant="solid" className="p-10 md:p-14 max-w-lg mx-auto rounded-[3rem] border border-white/5 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent" />
                
                <div className="text-center space-y-6 mb-12">
                    <div className="inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-cyan-500/10 border border-cyan-400/20 shadow-[0_0_30px_rgba(34,211,238,0.1)]">
                        <Zap className="h-10 w-10 text-cyan-400" />
                    </div>
                    <div className="space-y-2">
                        <h1 className="text-3xl md:text-4xl font-bold uppercase tracking-tight text-white">
                            Initialize Protocol
                        </h1>
                        <p className="text-zinc-600 font-bold uppercase tracking-[0.2em] text-[10px]">Authentication Required</p>
                    </div>
                </div>

                <form onSubmit={handleLogin} className="space-y-8">
                    <Input
                        label="PROTOCOL_ID"
                        type="text"
                        required
                        value={username}
                        onChange={(e) => {
                            setUsername(e.target.value);
                            if (fieldErrors.username) {
                                setFieldErrors(prev => ({...prev, username: undefined}));
                            }
                        }}
                        placeholder="ENTER_ID"
                        icon={<Mail className="h-5 w-5" />}
                        variant="solid"
                        className="rounded-2xl border-white/5 focus:border-cyan-400/50"
                        error={fieldErrors.username}
                    />

                    <Input
                        label="ACCESS_KEY"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => {
                            setPassword(e.target.value);
                            if (fieldErrors.password) {
                                setFieldErrors(prev => ({...prev, password: undefined}));
                            }
                        }}
                        placeholder="••••••••"
                        icon={<Lock className="h-5 w-5" />}
                        variant="solid"
                        className="rounded-2xl border-white/5 focus:border-cyan-400/50"
                        error={fieldErrors.password}
                    />

                    <div className="flex items-center justify-between">
                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={remember}
                                onChange={(e) => setRemember(e.target.checked)}
                                className="w-5 h-5 rounded-lg border-white/10 bg-black/60 text-cyan-400 focus:ring-cyan-400 transition-all"
                            />
                            <span className="text-zinc-500 text-xs font-bold uppercase tracking-widest group-hover:text-zinc-300 transition-colors">Persistent Link</span>
                        </label>
                    </div>

                    {error && (
                        <div className="p-5 rounded-2xl bg-red-500/5 border border-red-500/10 text-red-500 text-xs font-bold text-center uppercase tracking-widest" role="alert">
                            {error}
                        </div>
                    )}

                    <Button 
                        type="submit" 
                        variant="primary" 
                        size="lg"
                        isLoading={isLoading}
                        fullWidth
                        className="rounded-2xl py-8 font-bold tracking-[0.3em] uppercase text-xs"
                    >
                        {isLoading ? "Executing..." : "Initialize Session"}
                    </Button>
                </form>

                <div className="mt-12 pt-8 border-t border-white/5 text-center">
                    <p className="text-zinc-600 text-xs font-bold uppercase tracking-widest">
                        New Protocol?{" "}
                        <Link href="/register" className="text-cyan-400 hover:text-cyan-300 transition-colors">
                            Initialize Registry
                        </Link>
                    </p>
                </div>
            </Card>
        </BaseLayout>
    );
}


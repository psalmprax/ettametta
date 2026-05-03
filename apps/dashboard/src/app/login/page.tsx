"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, Lock } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { API_BASE } from "@/lib/config";
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
        <BaseLayout variant="auth">
            <Card variant="solid" className="p-12 md:p-16 max-w-lg mx-auto rounded-3xl border border-slate-200 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-linear-to-r from-transparent via-indigo-400 to-transparent" />
                
                <div className="text-center space-y-6 mb-12">
                    <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 border border-indigo-100 shadow-lg">
                        <Lock className="h-8 w-8 text-indigo-600" />
                    </div>
                    <div className="space-y-2">
                        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
                            Sign In
                        </h1>
                        <p className="text-slate-500 font-medium text-sm">Welcome back to Ettametta</p>
                    </div>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <Input
                        label="Username"
                        name="username"
                        type="text"
                        required
                        value={username}
                        onChange={(e) => {
                            setUsername(e.target.value);
                            if (fieldErrors.username) {
                                setFieldErrors(prev => ({...prev, username: undefined}));
                            }
                        }}
                        placeholder="Enter your username"
                        icon={<Mail className="h-5 w-5" />}
                        variant="default"
                        error={fieldErrors.username}
                    />

                    <Input
                        label="Password"
                        name="password"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => {
                            setPassword(e.target.value);
                            if (fieldErrors.password) {
                                setFieldErrors(prev => ({...prev, password: undefined}));
                            }
                        }}
                        placeholder="Enter your password"
                        icon={<Lock className="h-5 w-5" />}
                        variant="default"
                        error={fieldErrors.password}
                    />

                    <div className="flex items-center justify-between">
                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={remember}
                                onChange={(e) => setRemember(e.target.checked)}
                                className="w-5 h-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">Remember me</span>
                        </label>
                    </div>

                    {error && (
                        <div className="p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm font-medium text-center" role="alert">
                            {error}
                        </div>
                    )}

                    <Button 
                        type="submit" 
                        variant="primary" 
                        size="lg"
                        isLoading={isLoading}
                        fullWidth
                        className="rounded-xl py-4 font-semibold"
                    >
                        {isLoading ? "Signing in..." : "Sign In"}
                    </Button>

                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-200"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-white text-slate-500 font-medium">Or continue with</span>
                        </div>
                    </div>

                    <Button
                        type="button"
                        variant="outline"
                        size="lg"
                        fullWidth
                        onClick={() => window.location.href = `${API_BASE}/auth/google/login`}
                        className="rounded-xl py-4 border-slate-200 hover:bg-slate-50 transition-all flex items-center justify-center gap-3"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path
                                fill="#EA4335"
                                d="M12.48 10.92v3.28h7.84c-.24 1.84-1.92 5.4-7.84 5.4-5.12 0-9.28-4.24-9.28-9.44s4.16-9.44 9.28-9.44c2.96 0 4.96 1.28 6.08 2.32l2.56-2.48C19.6 1.84 16.48 0 12.48 0 5.6 0 0 5.6 0 12.48S5.6 24.96 12.48 24.96c6.48 0 10.72-4.56 10.72-10.88 0-.72-.08-1.28-.16-1.92h-10.56z"
                            />
                        </svg>
                        <span className="text-slate-700 font-semibold">Continue with Google</span>
                    </Button>
                </form>

                <div className="mt-8 pt-6 border-t border-slate-200 text-center">
                    <p className="text-slate-500 text-sm">
                        Don't have an account?{" "}
                        <Link href="/register" className="text-indigo-600 hover:text-indigo-700 font-semibold transition-colors">
                            Create account
                        </Link>
                    </p>
                </div>
            </Card>
        </BaseLayout>
    );
}

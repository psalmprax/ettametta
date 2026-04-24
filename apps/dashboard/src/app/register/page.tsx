"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, Loader2, Mail, Lock } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

import { API_BASE } from "@/lib/config";

export default function RegisterPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const { register } = useAuth();
    const router = useRouter();

    const validatePassword = (pass: string) => {
        if (pass.length < 8) return "Password must be at least 8 characters long";
        if (!/[A-Z]/.test(pass)) return "Password must contain at least one uppercase letter";
        if (!/[a-z]/.test(pass)) return "Password must contain at least one lowercase letter";
        if (!/[0-9]/.test(pass)) return "Password must contain at least one digit";
        return null;
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        
        const passError = validatePassword(password);
        if (passError) {
            setError(passError);
            return;
        }

        setIsLoading(true);
        setError("");

        try {
            const result = await register(email, password);
            if (result.success) {
                router.push("/login?registered=true");
            } else {
                setError(result.error || "Registration failed");
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
                    <div className="inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 border border-primary/20 animate-pulse">
                        <Zap className="h-10 w-10 text-primary fill-primary" />
                    </div>
                    <h1 className="text-5xl font-black uppercase tracking-tighter text-white">JOIN THE <span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-cyan-400 text-hollow">METTA</span></h1>
                    <p className="text-zinc-500 font-medium">Scale your content with AI precision</p>
                </div>

                <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                        <label htmlFor="email" className="text-xs font-black text-zinc-500 uppercase tracking-widest ml-1">Email</label>
                        <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-600 group-focus-within:text-primary transition-colors" />
                            <input
                                id="email"
                                name="email"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all text-white font-medium"
                                placeholder="you@example.com"
                            />
                        </div>
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
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all text-white font-medium"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm font-bold text-center animate-shake">
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
                                INITIALIZE ACCOUNT
                                <Zap className="h-4 w-4 fill-black group-hover:scale-125 transition-transform" />
                            </>
                        )}
                    </button>
                </form>

                <p className="text-center text-zinc-600 text-sm font-medium">
                    Already have access?{" "}
                    <Link href="/login" className="text-white hover:text-primary transition-colors">
                        Authenticated Login
                    </Link>
                </p>
            </div>
        </div>
    );
}

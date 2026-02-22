"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, Loader2, Mail, Lock } from "lucide-react";
import Link from "next/link";

import { API_BASE } from "@/lib/config";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

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
                localStorage.setItem("et_token", data.access_token);
                router.push("/");
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
                    <div className="inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-primary/10 border border-primary/20 animate-pulse">
                        <Zap className="h-10 w-10 text-primary fill-primary" />
                    </div>
                    <h1 className="text-5xl font-black italic uppercase tracking-tighter text-white">ETTA<span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-emerald-400 text-hollow">METTA</span></h1>
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
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all text-white font-medium"
                                placeholder="commander"
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
                                AUTHENTICATE
                                <Zap className="h-4 w-4 fill-black group-hover:scale-125 transition-transform" />
                            </>
                        )}
                    </button>
                </form>

                <p className="text-center text-zinc-600 text-sm font-medium">
                    New to ettametta?{" "}
                    <Link href="/register" className="text-white hover:text-primary transition-colors">
                        Register Access
                    </Link>
                </p>
            </div>
        </div>
    );
}

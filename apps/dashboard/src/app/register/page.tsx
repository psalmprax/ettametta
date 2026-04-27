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
        <BaseLayout variant="auth">
            <Card variant="solid" className="p-10 md:p-14 max-w-lg mx-auto rounded-[3rem] border border-white/5 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent" />
                
                <div className="text-center space-y-6 mb-12">
                    <div className="inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-cyan-500/10 border border-cyan-400/20 shadow-[0_0_30px_rgba(34,211,238,0.1)]">
                        <Zap className="h-10 w-10 text-cyan-400" />
                    </div>
                    <div className="space-y-2">
                        <h1 className="text-3xl md:text-4xl font-bold uppercase tracking-tight text-white">
                            Initialize Registry
                        </h1>
                        <p className="text-zinc-600 font-bold uppercase tracking-[0.2em] text-[10px]">Secure Protocol Enrollment</p>
                    </div>
                </div>

                <form onSubmit={handleRegister} className="space-y-8">
                    <Input
                        label="PROTOCOL_EMAIL"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="ENTER_EMAIL"
                        icon={<Mail className="h-5 w-5" />}
                        variant="cyber"
                        className="rounded-2xl border-white/5 focus:border-cyan-400/50"
                    />

                    <Input
                        label="ACCESS_KEY"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        icon={<Lock className="h-5 w-5" />}
                        variant="cyber"
                        className="rounded-2xl border-white/5 focus:border-cyan-400/50"
                        error={error}
                    />

                    <div className="bg-white/5 rounded-2xl p-6 text-[10px] text-zinc-500 space-y-3 border border-white/5">
                        <p className="font-bold text-zinc-400 uppercase tracking-widest">Key Requirements:</p>
                        <ul className="space-y-2 ml-2 font-bold uppercase tracking-widest">
                            <li className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-cyan-400 rounded-full" />
                                8+ Characters
                            </li>
                            <li className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-cyan-400 rounded-full" />
                                Alpha-Numeric Mix
                            </li>
                            <li className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-cyan-400 rounded-full" />
                                Upper/Lower Case
                            </li>
                        </ul>
                    </div>

                    <Button 
                        type="submit" 
                        variant="primary" 
                        size="lg"
                        isLoading={isLoading}
                        fullWidth
                        className="rounded-2xl py-8 font-bold tracking-[0.3em] uppercase text-xs"
                    >
                        {isLoading ? "Enrolling..." : "Register Protocol"}
                    </Button>
                </form>

                <div className="mt-12 pt-8 border-t border-white/5 text-center">
                    <p className="text-zinc-600 text-xs font-bold uppercase tracking-widest">
                        Already Synchronized?{" "}
                        <Link href="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors">
                            Initialize Session
                        </Link>
                    </p>
                </div>
            </Card>
        </BaseLayout>
    );
}

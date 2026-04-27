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
            // The register function in AuthContext already uses API_BASE correctly
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
            <Card variant="solid" className="p-12 md:p-16 max-w-lg mx-auto rounded-3xl border border-slate-200 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-indigo-400 to-transparent" />
                
                <div className="text-center space-y-6 mb-12">
                    <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 border border-indigo-100 shadow-lg">
                        <Zap className="h-8 w-8 text-indigo-600" />
                    </div>
                    <div className="space-y-2">
                        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
                            Create Account
                        </h1>
                        <p className="text-slate-500 font-medium text-sm">Join Ettametta today</p>
                    </div>
                </div>

                <form onSubmit={handleRegister} className="space-y-6">
                    <Input
                        label="Email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        icon={<Mail className="h-5 w-5" />}
                        variant="default"
                        error={error}
                    />

                    <Input
                        label="Password"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Create a secure password"
                        icon={<Lock className="h-5 w-5" />}
                        variant="default"
                        error={error}
                    />

                    <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-600 space-y-2">
                        <p className="font-semibold text-slate-800">Password Requirements:</p>
                        <ul className="space-y-1 ml-4 text-sm">
                            <li className="flex items-center gap-2 text-slate-600">
                                <span className="w-1 h-1 bg-indigo-500 rounded-full" />
                                8+ characters
                            </li>
                            <li className="flex items-center gap-2 text-slate-600">
                                <span className="w-1 h-1 bg-indigo-500 rounded-full" />
                                Uppercase and lowercase letters
                            </li>
                            <li className="flex items-center gap-2 text-slate-600">
                                <span className="w-1 h-1 bg-indigo-500 rounded-full" />
                                At least one number
                            </li>
                        </ul>
                    </div>

                    <Button 
                        type="submit" 
                        variant="primary" 
                        size="lg"
                        isLoading={isLoading}
                        fullWidth
                        className="rounded-xl py-4 font-semibold"
                    >
                        {isLoading ? "Creating Account..." : "Create Account"}
                    </Button>
                </form>

                <div className="mt-8 pt-6 border-t border-slate-200 text-center">
                    <p className="text-slate-500 text-sm">
                        Already have an account?{" "}
                        <Link href="/login" className="text-indigo-600 hover:text-indigo-700 font-semibold transition-colors">
                            Sign in
                        </Link>
                    </p>
                </div>
            </Card>
        </BaseLayout>
    );
}

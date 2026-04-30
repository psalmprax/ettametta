"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { BaseLayout } from "@/components/layout/BaseLayout";

function CallbackHandler() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login } = useAuth();

    useEffect(() => {
        const token = searchParams.get("token");
        const error = searchParams.get("error");

        if (error) {
            console.error("OAuth Error:", error);
            router.push(`/login?error=${encodeURIComponent(error)}`);
            return;
        }

        if (token) {
            // Standard: Finalize Identity Handshake
            login(token, true)
                .then(() => {
                    // Success! Redirect to secure dashboard
                    router.push("/dashboard");
                })
                .catch((err) => {
                    console.error("Session verification failed:", err);
                    router.push("/login?error=Session+verification+failed");
                });
        } else {
            // No token found, redirect back to login
            router.push("/login");
        }
    }, [searchParams, login, router]);

    return (
        <div className="flex flex-col items-center justify-center space-y-6">
            <Loader2 className="h-12 w-12 text-indigo-600 animate-spin" />
            <div className="text-center">
                <h2 className="text-xl font-bold text-slate-900">Finalizing Identity</h2>
                <p className="text-slate-500">Securing your session in the Intelligence OS...</p>
            </div>
        </div>
    );
}

export default function AuthCallbackPage() {
    return (
        <BaseLayout variant="auth">
            <Card variant="solid" className="p-16 max-w-md mx-auto rounded-3xl border border-slate-200 shadow-xl">
                <Suspense fallback={
                    <div className="flex justify-center">
                        <Loader2 className="h-12 w-12 text-indigo-600 animate-spin" />
                    </div>
                }>
                    <CallbackHandler />
                </Suspense>
            </Card>
        </BaseLayout>
    );
}

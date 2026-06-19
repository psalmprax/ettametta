"use client";

import React, { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import AdminContent from "@/components/admin/AdminContent";

export default function AdminSettingsPage() {
    const { user, isLoading: authLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!authLoading && (!user || (user.role !== "admin" && user.role !== "super_admin"))) {
            router.push("/");
        }
    }, [authLoading, user, router]);

    if (authLoading || !user || (user.role !== "admin" && user.role !== "super_admin")) {
        return <div className="h-screen bg-black" />;
    }

    return <AdminContent />;
}

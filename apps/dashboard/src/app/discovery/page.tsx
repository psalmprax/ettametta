"use client";

import React, { Suspense } from "react";
import { DiscoveryContent } from "./components/DiscoveryContent";

export default function DiscoveryPage() {
    return (
        <Suspense fallback={null}>
            <DiscoveryContent />
        </Suspense>
    );
}

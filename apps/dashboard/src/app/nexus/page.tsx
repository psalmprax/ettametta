"use client";

import React, { Suspense } from "react";
import NexusContent from "./components/NexusContent";

export default function NexusPage() {
    return (
        <Suspense fallback={null}>
            <NexusContent />
        </Suspense>
    );
}

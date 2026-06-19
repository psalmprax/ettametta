"use client";

import React, { Suspense } from "react";
import { CreationContent } from "./components/CreationContent";

export default function CreationPage() {
    return (
        <Suspense fallback={null}>
            <CreationContent />
        </Suspense>
    );
}

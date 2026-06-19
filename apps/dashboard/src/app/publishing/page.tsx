"use client";

import React from "react";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import PublishingContent from "./components/PublishingContent";

export default function PublishingPage() {
    return (
        <CommandCenterLayout
            title="EGRESS HUB"
            subtitle="GLOBAL_DISTRIBUTION_MATRIX_V3.0"
        >
            <PublishingContent />
        </CommandCenterLayout>
    );
}

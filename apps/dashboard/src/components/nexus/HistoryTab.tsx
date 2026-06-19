"use client";

import React from "react";
import { DesignCard } from "@/components/ui/DesignCard";
import { NexusJob } from "@/lib/types";

interface Props {
    nexusJobs: NexusJob[];
    handlePreviewScenes: (jobId: string) => void;
    handleDeleteJob: (jobId: string) => void;
}

export default function HistoryTab({
    nexusJobs,
    handlePreviewScenes,
    handleDeleteJob,
}: Props) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar p-1">
            {nexusJobs?.map((job) => (
                <DesignCard
                    key={job.id}
                    title={`PIPELINE_${job.id}`}
                    status={job.status}
                    metrics={[
                        {
                            label: "Completion",
                            value: `${job.progress || 0}%`,
                            progress: job.progress,
                            color: "text-cyan-400",
                        },
                        { label: "Niche", value: job.niche, color: "text-zinc-500" },
                    ]}
                    footerInfo={new Date(job.created_at).toLocaleString()}
                    toolsStatus="Verified"
                    onRefresh={() => handlePreviewScenes(job.id)}
                    onDelete={() => handleDeleteJob(job.id)}
                />
            ))}
        </div>
    );
}

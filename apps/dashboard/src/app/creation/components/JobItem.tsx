"use client";

import React from "react";
import { PlaySquare, FileVideo } from "lucide-react";

export function JobItem({ job }: { readonly job: any }) {
    let statusColor = 'bg-yellow-500/20 text-yellow-400';
    const status = job.status?.toLowerCase();
    
    if (status === 'completed') {
        statusColor = 'bg-emerald-500/20 text-emerald-400';
    } else if (status === 'failed') {
        statusColor = 'bg-rose-500/20 text-rose-400';
    }

    return (
        <div className="p-3 bg-white/5 rounded-lg border border-white/5">
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-white truncate flex-1">{job.title || job.prompt || "Remix Video"}</span>
                <span className={`text-[8px] px-2 py-1 rounded-full ml-2 ${statusColor}`}>
                    {status === 'processing' ? 'PROCESSING' : (job.status?.toUpperCase() || 'UNKNOWN')}
                </span>
            </div>
            
            {/* Progress bar for processing jobs */}
            {job.status === 'processing' && job.progress !== undefined && (
                <div className="mb-2">
                    <div className="flex justify-between text-[8px] text-zinc-500 mb-1">
                        <span>{job.current_step || 'Processing...'}</span>
                        <span>{job.progress}%</span>
                    </div>
                    <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                        <div 
                            className="h-full bg-violet-500 transition-all duration-500"
                            style={{ width: `${job.progress}%` }}
                        />
                    </div>
                </div>
            )}
            
            <span className="text-[8px] text-zinc-500 block mb-2">
                {new Date(job.created_at).toLocaleString()}
            </span>
            
            {/* Preview and Download buttons for completed videos */}
            {(job.status === 'completed' || job.status === 'COMPLETED') && (job.output_path || job.result?.output_path) && (
                <div className="flex gap-2 mt-2">
                    <button
                        onClick={() => window.open(`/api/v1/video/preview/${job.id}`, '_blank')}
                        className="flex-1 px-3 py-1.5 bg-violet-500/20 hover:bg-violet-500/30 text-violet-400 text-[9px] font-bold uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center gap-1"
                    >
                        <PlaySquare className="h-3 w-3" />
                        Preview
                    </button>
                    <button
                        onClick={() => {
                            const link = document.createElement('a');
                            link.href = `/api/v1/video/download/${job.id}`;
                            link.download = `remix_${job.id}.mp4`;
                            link.click();
                        }}
                        className="flex-1 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-[9px] font-bold uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center gap-1"
                    >
                        <FileVideo className="h-3 w-3" />
                        Download
                    </button>
                </div>
            )}
        </div>
    );
}

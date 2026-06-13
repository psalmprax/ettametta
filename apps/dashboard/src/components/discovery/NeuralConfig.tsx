"use client";

import React, { memo } from "react";
import { Filter } from "lucide-react";
import { motion } from "framer-motion";

// Neural Config Component - Extracted from discovery page
interface NeuralConfigProps {
    minViralScore: number;
    excludeShorts: boolean;
    onMinViralScoreChange: (value: number) => void;
    onExcludeShortsChange: (value: boolean) => void;
}

export const NeuralConfig = memo<NeuralConfigProps>(function NeuralConfig({
    minViralScore,
    excludeShorts,
    onMinViralScoreChange,
    onExcludeShortsChange
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6 space-y-4"
        >
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Filter className="h-5 w-5 text-primary" />
                Neural Discovery Config
            </h3>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">
                        Minimum Viral Score: {minViralScore}
                    </label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={minViralScore}
                        onChange={(e) => onMinViralScoreChange(Number(e.target.value))}
                        className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                </div>

                <div className="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        id="excludeShorts"
                        checked={excludeShorts}
                        onChange={(e) => onExcludeShortsChange(e.target.checked)}
                        className="w-4 h-4 bg-zinc-900 border border-zinc-800 rounded focus:ring-primary focus:ring-2"
                    />
                    <label htmlFor="excludeShorts" className="text-sm font-medium text-zinc-300">
                        Exclude Shorts (&lt; 60s)
                    </label>
                </div>
            </div>
        </motion.div>
    );
});
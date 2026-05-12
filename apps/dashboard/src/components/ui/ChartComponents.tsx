"use client";

import React from "react";
import { 
    XAxis as RechartsXAxis, 
    YAxis as RechartsYAxis, 
    Tooltip as RechartsTooltip,
    ResponsiveContainer as RechartsResponsiveContainer,
    AreaChart as RechartsAreaChart,
    Area as RechartsArea,
    CartesianGrid as RechartsCartesianGrid
} from "recharts";
import { cn } from "@/lib/utils";

// --- Custom Tooltip ---

export const ChartTooltip = ({ active, payload, label, prefix = "", suffix = "" }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-[#0F0F11]/95 backdrop-blur-xl border border-white/10 p-3 rounded-xl shadow-2xl min-w-[120px]">
                <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2 border-b border-white/5 pb-1">
                    {label || "Telemetry Node"}
                </p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                            <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
                            <span className="text-[10px] font-bold text-zinc-300 uppercase">{entry.name}</span>
                        </div>
                        <span className="text-xs font-black text-white font-mono">
                            {prefix}{entry.value.toLocaleString()}{suffix}
                        </span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

// --- Standardized Axes ---

export const ChartXAxis = (props: any) => (
    <RechartsXAxis
        axisLine={false}
        tickLine={false}
        tick={{ fill: "rgba(255,255,255,0.2)", fontSize: 9, fontWeight: 700 }}
        dy={10}
        {...props}
    />
);

export const ChartYAxis = (props: any) => (
    <RechartsYAxis
        axisLine={false}
        tickLine={false}
        tick={{ fill: "rgba(255,255,255,0.2)", fontSize: 9, fontWeight: 700 }}
        dx={-10}
        {...props}
    />
);

export const ChartGrid = (props: any) => (
    <RechartsCartesianGrid
        strokeDasharray="3 3"
        stroke="rgba(255,255,255,0.03)"
        vertical={false}
        {...props}
    />
);

// --- High Density Area Chart Wrapper ---

interface AreaChartProps {
    data: any[];
    dataKey: string;
    color?: string;
    height?: number | string;
    showGrid?: boolean;
    showTooltip?: boolean;
    gradientId?: string;
}

export const AreaChartCustom = ({
    data,
    dataKey,
    color = "#8b5cf6",
    height = 300,
    showGrid = true,
    showTooltip = true,
    gradientId = "chartGradient"
}: AreaChartProps) => {
    return (
        <div style={{ width: "100%", height }}>
            <RechartsResponsiveContainer width="100%" height="100%">
                <RechartsAreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    {showGrid && <ChartGrid />}
                    <ChartXAxis dataKey="time" hide />
                    <ChartYAxis hide />
                    {showTooltip && <RechartsTooltip content={<ChartTooltip />} cursor={{ stroke: "rgba(255,255,255,0.1)", strokeWidth: 1 }} />}
                    <RechartsArea
                        type="monotone"
                        dataKey={dataKey}
                        stroke={color}
                        strokeWidth={3}
                        fillOpacity={1}
                        fill={`url(#${gradientId})`}
                        animationDuration={1500}
                    />
                </RechartsAreaChart>
            </RechartsResponsiveContainer>
        </div>
    );
};

// --- Mini Area Chart for Cards ---

export const MiniAreaChart = ({ data, color = "#22d3ee", height = 40 }: { data: any[], color?: string, height?: number }) => {
    return (
        <div style={{ width: "100%", height }}>
            <RechartsResponsiveContainer width="100%" height="100%">
                <RechartsAreaChart data={data}>
                    <defs>
                        <linearGradient id="miniGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.2} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <RechartsArea
                        type="monotone"
                        dataKey="value"
                        stroke={color}
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#miniGradient)"
                        animationDuration={1000}
                    />
                </RechartsAreaChart>
            </RechartsResponsiveContainer>
        </div>
    );
};

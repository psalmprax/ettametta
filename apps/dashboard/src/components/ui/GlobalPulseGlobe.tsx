"use client";

import React, { useRef, useEffect, useMemo, useState } from "react";

/**
 * 2D SVG Neural Globe — React 19 compatible replacement for R3F version.
 * Renders a rotating wireframe sphere with animated nodes and connections.
 */
export default React.memo(function GlobalPulseGlobe({ pulseIntensity = 1 }: { pulseIntensity?: number }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const frameRef = useRef<number>(0);
    const [hovered, setHovered] = useState(false);

    const nodes = useMemo(() => {
        const count = 80;
        const pts: { x: number; y: number; z: number }[] = [];
        for (let i = 0; i < count; i++) {
            const phi = Math.acos(-1 + (2 * i) / count);
            const theta = Math.sqrt(count * Math.PI) * phi;
            pts.push({
                x: Math.sin(phi) * Math.cos(theta),
                y: Math.sin(phi) * Math.sin(theta),
                z: Math.cos(phi),
            });
        }
        return pts;
    }, []);

    const connections = useMemo(() => {
        const lines: [number, number][] = [];
        const maxDist = 0.8;
        for (let i = 0; i < nodes.length; i++) {
            let matches = 0;
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[i].x - nodes[j].x;
                const dy = nodes[i].y - nodes[j].y;
                const dz = nodes[i].z - nodes[j].z;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
                if (dist < maxDist && matches < 3) {
                    lines.push([i, j]);
                    matches++;
                }
            }
        }
        return lines;
    }, [nodes]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let angle = 0;
        const speed = 0.003;

        const project = (x: number, y: number, z: number, cx: number, cy: number, r: number) => {
            const cosA = Math.cos(angle);
            const sinA = Math.sin(angle);
            const rx = x * cosA - z * sinA;
            const rz = x * sinA + z * cosA;
            const scale = 1 / (1 + rz * 0.3);
            return {
                px: cx + rx * r * scale,
                py: cy + y * r * scale,
                depth: rz,
                scale,
            };
        };

        const draw = () => {
            if (!canvas || !ctx) return;
            const w = canvas.width;
            const h = canvas.height;
            const cx = w / 2;
            const cy = h / 2;
            const r = Math.min(w, h) * 0.38;

            ctx.clearRect(0, 0, w, h);

            // Globe outline
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(0, 242, 255, 0.08)";
            ctx.lineWidth = 1;
            ctx.stroke();

            // Latitude lines
            for (let lat = -60; lat <= 60; lat += 30) {
                const latRad = (lat * Math.PI) / 180;
                const y = Math.sin(latRad);
                const rr = Math.cos(latRad);
                ctx.beginPath();
                for (let lon = 0; lon <= 360; lon += 5) {
                    const lonRad = (lon * Math.PI) / 180;
                    const x = rr * Math.cos(lonRad);
                    const z = rr * Math.sin(lonRad);
                    const p = project(x, y, z, cx, cy, r);
                    if (lon === 0) ctx.moveTo(p.px, p.py);
                    else ctx.lineTo(p.px, p.py);
                }
                ctx.strokeStyle = "rgba(0, 242, 255, 0.04)";
                ctx.stroke();
            }

            // Connections
            ctx.strokeStyle = `rgba(0, 242, 255, ${0.05 + pulseIntensity * 0.15})`;
            ctx.lineWidth = 0.5;
            for (const [a, b] of connections) {
                const pa = project(nodes[a].x, nodes[a].y, nodes[a].z, cx, cy, r);
                const pb = project(nodes[b].x, nodes[b].y, nodes[b].z, cx, cy, r);
                const avgDepth = (pa.depth + pb.depth) / 2;
                if (avgDepth > -0.5) {
                    ctx.globalAlpha = 0.3 + avgDepth * 0.4;
                    ctx.beginPath();
                    ctx.moveTo(pa.px, pa.py);
                    ctx.lineTo(pb.px, pb.py);
                    ctx.stroke();
                }
            }
            ctx.globalAlpha = 1;

            // Nodes
            for (const node of nodes) {
                const p = project(node.x, node.y, node.z, cx, cy, r);
                if (p.depth > -0.3) {
                    const size = 1.5 * p.scale * (1 + pulseIntensity * 0.3);
                    const alpha = 0.3 + p.depth * 0.5 + pulseIntensity * 0.3;
                    ctx.beginPath();
                    ctx.arc(p.px, p.py, size, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(0, 242, 255, ${Math.min(1, Math.max(0.1, alpha))})`;
                    ctx.fill();
                }
            }

            angle += speed * (hovered ? 2 : 1);
            frameRef.current = requestAnimationFrame(draw);
        };

        const resizeCanvas = () => {
            const rect = canvas.parentElement?.getBoundingClientRect();
            if (rect) {
                canvas.width = rect.width * window.devicePixelRatio;
                canvas.height = rect.height * window.devicePixelRatio;
                ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
            }
        };

        resizeCanvas();
        draw();

        const ro = new ResizeObserver(resizeCanvas);
        if (canvas.parentElement) ro.observe(canvas.parentElement);

        return () => {
            cancelAnimationFrame(frameRef.current);
            ro.disconnect();
        };
    }, [nodes, connections, pulseIntensity, hovered]);

    return (
        <div
            className="h-[600px] w-full relative bg-zinc-950/30 rounded-lg overflow-hidden"
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            <canvas
                ref={canvasRef}
                className="absolute inset-0 w-full h-full"
                style={{ imageRendering: "auto" }}
            />
            <div className="absolute bottom-4 left-4 text-xs text-zinc-500">
                Neural Globe
            </div>
        </div>
    );
});

"use client";

import React, { useRef, useEffect, useMemo, useState } from "react";

interface GeoHotspot {
    name: string;
    lat: number;
    lng: number;
}

interface TelemetryData {
    metrics?: {
        global_velocity?: number;
        signal_strength?: number;
        active_nodes?: number;
    };
    geo_activity?: Array<{ lat: number; lng: number; intensity: number }>;
    load_avg?: number;
}

interface GlobalPulseGlobeProps {
    readonly pulseIntensity?: number;
    readonly telemetry?: TelemetryData | null;
    readonly reducedMotion?: boolean;
}

const CITIES: GeoHotspot[] = [
    { name: "Lagos", lat: 6.5244, lng: 3.3792 },
    { name: "NYC", lat: 40.7128, lng: -74.006 },
    { name: "London", lat: 51.5074, lng: -0.1278 },
    { name: "Singapore", lat: 1.3521, lng: 103.8198 },
];

const REGION_ARCS = [
    { name: "Americas", centerLng: -80, color: "0, 242, 255", baseBrightness: 0.7 },
    { name: "Europe", centerLng: 15, color: "139, 92, 246", baseBrightness: 0.9 },
    { name: "Africa", centerLng: 25, color: "245, 158, 11", baseBrightness: 0.6 },
    { name: "Asia-Pacific", centerLng: 105, color: "16, 185, 129", baseBrightness: 0.8 },
];

function latLngToPoint(lat: number, lng: number) {
    const phi = ((90 - lat) * Math.PI) / 180;
    const theta = ((lng + 180) * Math.PI) / 180;
    return {
        x: -Math.sin(phi) * Math.cos(theta),
        y: Math.cos(phi),
        z: Math.sin(phi) * Math.sin(theta),
    };
}

interface Particle {
    fromIdx: number;
    toIdx: number;
    progress: number;
    speed: number;
}

export default React.memo(function GlobalPulseGlobe({
    pulseIntensity = 1,
    telemetry = null,
    reducedMotion = false,
}: GlobalPulseGlobeProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const frameRef = useRef<number>(0);
    const [hovered, setHovered] = useState(false);
    const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
    const particlesRef = useRef<Particle[]>([]);
    const pulseWaveRef = useRef(0);

    // Detect prefers-reduced-motion with reactive state
    useEffect(() => {
        if (typeof window === "undefined") return;
        const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
        setPrefersReducedMotion(mq.matches);
        const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
        mq.addEventListener("change", handler);
        return () => mq.removeEventListener("change", handler);
    }, []);

    const effectiveReducedMotion = reducedMotion || prefersReducedMotion;

    // Compute telemetry-driven intensity
    const computedIntensity = useMemo(() => {
        if (!telemetry?.metrics) return pulseIntensity;
        const velocity = telemetry.metrics.global_velocity ?? 1;
        const signal = (telemetry.metrics.signal_strength ?? 80) / 100;
        return Math.max(0.2, Math.min(2, velocity * signal * pulseIntensity));
    }, [telemetry, pulseIntensity]);

    // Sphere nodes (Fibonacci distribution)
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

    // City 3D positions
    const cityPoints = useMemo(() => CITIES.map((c) => latLngToPoint(c.lat, c.lng)), []);

    // Pre-compute region arc geometry (avoid nested loops per frame)
    const regionArcPaths = useMemo(() => {
        return REGION_ARCS.map((region) => {
            const centerRad = ((region.centerLng + 180) * Math.PI) / 180;
            const arcSpan = 40 * (Math.PI / 180);
            const lines: { x: number; y: number; z: number }[][] = [];

            for (let latStep = -50; latStep <= 50; latStep += 10) {
                const latRad = (latStep * Math.PI) / 180;
                const pts: { x: number; y: number; z: number }[] = [];
                for (let t = -arcSpan; t <= arcSpan; t += 0.08) {
                    const lon = centerRad + t;
                    pts.push({
                        x: Math.cos(latRad) * Math.cos(lon),
                        y: Math.sin(latRad),
                        z: Math.cos(latRad) * Math.sin(lon),
                    });
                }
                lines.push(pts);
            }
            return { ...region, lines };
        });
    }, []);

    // Connections between nearby nodes
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

    // Interconnections between cities
    const cityConnections = useMemo(() => {
        const lines: [number, number][] = [];
        for (let i = 0; i < cityPoints.length; i++) {
            for (let j = i + 1; j < cityPoints.length; j++) {
                lines.push([i, j]);
            }
        }
        return lines;
    }, [cityPoints]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let angle = 0;
        const speed = effectiveReducedMotion ? 0 : 0.003;

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

        // Initialize particles
        if (particlesRef.current.length === 0) {
            particlesRef.current = cityConnections.map(([from, to]) => ({
                fromIdx: from,
                toIdx: to,
                progress: Math.random(),
                speed: 0.002 + Math.random() * 0.003,
            }));
        }

        let currentDPR = 1;

        const resizeCanvas = () => {
            const rect = canvas.parentElement?.getBoundingClientRect();
            if (!rect) return;
            const dpr = window.devicePixelRatio || 1;
            currentDPR = dpr;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            // Reset transform before applying new DPR scale
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        };

        const draw = () => {
            if (!canvas || !ctx) return;
            // Reset transform each frame to avoid accumulation
            ctx.setTransform(currentDPR, 0, 0, currentDPR, 0, 0);

            const w = canvas.width / currentDPR;
            const h = canvas.height / currentDPR;
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

            // Region arcs with varying brightness (pre-computed geometry)
            const now = Date.now();
            for (const region of regionArcPaths) {
                const brightnessOscillation = effectiveReducedMotion
                    ? region.baseBrightness
                    : region.baseBrightness * (0.7 + 0.3 * Math.sin(now * 0.001 + region.centerLng * 0.1));

                const alpha = brightnessOscillation * computedIntensity * 0.15;

                ctx.strokeStyle = `rgba(${region.color}, ${Math.min(0.6, alpha)})`;
                ctx.lineWidth = 2;

                for (const line of region.lines) {
                    ctx.beginPath();
                    for (let k = 0; k < line.length; k++) {
                        const p = project(line[k].x, line[k].y, line[k].z, cx, cy, r * 1.01);
                        if (k === 0) ctx.moveTo(p.px, p.py);
                        else ctx.lineTo(p.px, p.py);
                    }
                    ctx.stroke();
                }
            }

            // Pulse waves radiating from center
            if (!effectiveReducedMotion) {
                pulseWaveRef.current += 0.02 * computedIntensity;
                const waveCount = 3;
                for (let i = 0; i < waveCount; i++) {
                    const phase = (pulseWaveRef.current + i * (1 / waveCount)) % 1;
                    const waveR = r * phase;
                    const waveAlpha = (1 - phase) * 0.15 * computedIntensity;
                    ctx.beginPath();
                    ctx.arc(cx, cy, waveR, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(0, 242, 255, ${Math.max(0, waveAlpha)})`;
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }
            }

            // Connections
            ctx.strokeStyle = `rgba(0, 242, 255, ${0.05 + computedIntensity * 0.15})`;
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
                    const size = 1.5 * p.scale * (1 + computedIntensity * 0.3);
                    const alpha = 0.3 + p.depth * 0.5 + computedIntensity * 0.3;
                    ctx.beginPath();
                    ctx.arc(p.px, p.py, size, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(0, 242, 255, ${Math.min(1, Math.max(0.1, alpha))})`;
                    ctx.fill();
                }
            }

            // City connections (dim lines)
            ctx.lineWidth = 0.5;
            for (const [a, b] of cityConnections) {
                const pa = project(cityPoints[a].x, cityPoints[a].y, cityPoints[a].z, cx, cy, r);
                const pb = project(cityPoints[b].x, cityPoints[b].y, cityPoints[b].z, cx, cy, r);
                const avgDepth = (pa.depth + pb.depth) / 2;
                if (avgDepth > -0.3) {
                    ctx.strokeStyle = `rgba(139, 92, 246, ${0.08 + avgDepth * 0.1})`;
                    ctx.beginPath();
                    ctx.moveTo(pa.px, pa.py);
                    ctx.lineTo(pb.px, pb.py);
                    ctx.stroke();
                }
            }

            // Data particles flowing along city connections
            if (!effectiveReducedMotion) {
                for (const particle of particlesRef.current) {
                    particle.progress = (particle.progress + particle.speed * computedIntensity) % 1;

                    const fromPt = cityPoints[particle.fromIdx];
                    const toPt = cityPoints[particle.toIdx];

                    // Interpolate along great circle (slerp approximation)
                    const t = particle.progress;
                    const ix = fromPt.x * (1 - t) + toPt.x * t;
                    const iy = fromPt.y * (1 - t) + toPt.y * t;
                    const iz = fromPt.z * (1 - t) + toPt.z * t;
                    const len = Math.sqrt(ix * ix + iy * iy + iz * iz);
                    const nx = ix / len;
                    const ny = iy / len;
                    const nz = iz / len;

                    const p = project(nx, ny, nz, cx, cy, r);
                    if (p.depth > -0.2) {
                        const particleSize = 2.5 * p.scale;
                        const particleAlpha = (0.5 + p.depth * 0.3) * computedIntensity;

                        // Glow
                        const gradient = ctx.createRadialGradient(p.px, p.py, 0, p.px, p.py, particleSize * 3);
                        gradient.addColorStop(0, `rgba(139, 92, 246, ${Math.min(1, particleAlpha * 0.8)})`);
                        gradient.addColorStop(1, "rgba(139, 92, 246, 0)");
                        ctx.beginPath();
                        ctx.arc(p.px, p.py, particleSize * 3, 0, Math.PI * 2);
                        ctx.fillStyle = gradient;
                        ctx.fill();

                        // Core
                        ctx.beginPath();
                        ctx.arc(p.px, p.py, particleSize, 0, Math.PI * 2);
                        ctx.fillStyle = `rgba(200, 170, 255, ${Math.min(1, particleAlpha)})`;
                        ctx.fill();
                    }
                }
            }

            // Geo hotspots (city markers)
            for (let i = 0; i < cityPoints.length; i++) {
                const cp = cityPoints[i];
                const p = project(cp.x, cp.y, cp.z, cx, cy, r);
                if (p.depth > -0.2) {
                    // Check if telemetry has geo_activity for this city
                    const geoMatch = telemetry?.geo_activity?.find(
                        (g) => Math.abs(g.lat - CITIES[i].lat) < 10 && Math.abs(g.lng - CITIES[i].lng) < 15
                    );
                    const cityIntensity = geoMatch ? geoMatch.intensity : 0.5 + 0.3 * Math.sin(now * 0.002 + i);

                    const pulseSize = effectiveReducedMotion
                        ? 4 * p.scale
                        : (4 + 2 * Math.sin(now * 0.003 + i * 1.5)) * p.scale;

                    const outerSize = pulseSize * (2 + cityIntensity);
                    const alpha = (0.3 + cityIntensity * 0.5) * p.depth;

                    // Outer pulse ring
                    if (!effectiveReducedMotion) {
                        const ringPhase = (now * 0.002 + i * 0.8) % 1;
                        const ringR = outerSize * (1 + ringPhase * 2);
                        const ringAlpha = (1 - ringPhase) * 0.3 * computedIntensity;
                        ctx.beginPath();
                        ctx.arc(p.px, p.py, ringR, 0, Math.PI * 2);
                        ctx.strokeStyle = `rgba(139, 92, 246, ${Math.max(0, ringAlpha)})`;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }

                    // Glow
                    const glow = ctx.createRadialGradient(p.px, p.py, 0, p.px, p.py, outerSize);
                    glow.addColorStop(0, `rgba(139, 92, 246, ${Math.min(0.8, alpha * computedIntensity)})`);
                    glow.addColorStop(0.5, `rgba(139, 92, 246, ${Math.min(0.3, alpha * 0.3)})`);
                    glow.addColorStop(1, "rgba(139, 92, 246, 0)");
                    ctx.beginPath();
                    ctx.arc(p.px, p.py, outerSize, 0, Math.PI * 2);
                    ctx.fillStyle = glow;
                    ctx.fill();

                    // Core dot
                    ctx.beginPath();
                    ctx.arc(p.px, p.py, pulseSize, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(200, 170, 255, ${Math.min(1, alpha * 1.5)})`;
                    ctx.fill();

                    // City label
                    if (p.depth > 0.2) {
                        ctx.font = `${Math.round(9 * p.scale)}px monospace`;
                        ctx.fillStyle = `rgba(200, 170, 255, ${Math.min(0.7, p.depth * 0.8)})`;
                        ctx.textAlign = "center";
                        ctx.fillText(CITIES[i].name.toUpperCase(), p.px, p.py - pulseSize - 6);
                    }
                }
            }

            if (!effectiveReducedMotion) {
                angle += speed * (hovered ? 2 : 1);
            }
            frameRef.current = requestAnimationFrame(draw);
        };

        resizeCanvas();
        draw();

        const ro = new ResizeObserver(resizeCanvas);
        if (canvas.parentElement) ro.observe(canvas.parentElement);

        return () => {
            cancelAnimationFrame(frameRef.current);
            ro.disconnect();
        };
    }, [nodes, connections, cityPoints, cityConnections, regionArcPaths, computedIntensity, hovered, effectiveReducedMotion, telemetry]);

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
                Neural Globe {effectiveReducedMotion ? "(Reduced Motion)" : ""}
            </div>
        </div>
    );
});

"use client";

import React, { useRef, useEffect } from "react";

/**
 * 2D Canvas replacement for R3F NeuralCore.
 * Renders a wireframe sphere with floating particles — decorative background.
 */
export default function NeuralCore() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const frameRef = useRef<number>(0);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const particleCount = 2000;
        const particles: { x: number; y: number; z: number; vx: number; vy: number; vz: number }[] = [];
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: (Math.random() - 0.5) * 15,
                y: (Math.random() - 0.5) * 15,
                z: (Math.random() - 0.5) * 15,
                vx: (Math.random() - 0.5) * 0.002,
                vy: (Math.random() - 0.5) * 0.002,
                vz: (Math.random() - 0.5) * 0.002,
            });
        }

        // Sphere wireframe points
        const sphereLines: { x: number; y: number; z: number }[][] = [];
        const sphereR = 1.5;
        const segments = 24;
        // Latitude lines
        for (let lat = -segments / 2; lat <= segments / 2; lat++) {
            const phi = (lat / segments) * Math.PI;
            const ringR = Math.sin(phi) * sphereR;
            const y = Math.cos(phi) * sphereR;
            const pts: { x: number; y: number; z: number }[] = [];
            for (let lon = 0; lon <= segments * 2; lon++) {
                const theta = (lon / (segments * 2)) * Math.PI * 2;
                pts.push({ x: ringR * Math.cos(theta), y, z: ringR * Math.sin(theta) });
            }
            sphereLines.push(pts);
        }
        // Longitude lines
        for (let lon = 0; lon < segments; lon++) {
            const theta = (lon / segments) * Math.PI;
            const pts: { x: number; y: number; z: number }[] = [];
            for (let lat = 0; lat <= segments * 2; lat++) {
                const phi = (lat / (segments * 2)) * Math.PI;
                pts.push({
                    x: sphereR * Math.sin(phi) * Math.cos(theta),
                    y: sphereR * Math.cos(phi),
                    z: sphereR * Math.sin(phi) * Math.sin(theta),
                });
            }
            sphereLines.push(pts);
        }

        let rotY = 0;
        let rotX = 0;
        let floatOffset = 0;

        const resizeCanvas = () => {
            const rect = canvas.parentElement?.getBoundingClientRect();
            if (!rect) return;
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        };

        const draw = () => {
            if (!canvas || !ctx) return;
            const dpr = window.devicePixelRatio || 1;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

            const w = canvas.width / dpr;
            const h = canvas.height / dpr;
            const cx = w / 2;
            const cy = h / 2 + Math.sin(floatOffset) * 15;
            const scale = Math.min(w, h) / 8;

            ctx.clearRect(0, 0, w, h);

            const cosY = Math.cos(rotY);
            const sinY = Math.sin(rotY);
            const cosX = Math.cos(rotX);
            const sinX = Math.sin(rotX);

            const project = (x: number, y: number, z: number) => {
                // Rotate Y
                let rx = x * cosY - z * sinY;
                let rz = x * sinY + z * cosY;
                // Rotate X
                let ry = y * cosX - rz * sinX;
                rz = y * sinX + rz * cosX;
                const perspective = 1 / (1 + rz * 0.1);
                return {
                    px: cx + rx * scale * perspective,
                    py: cy + ry * scale * perspective,
                    depth: rz,
                    perspective,
                };
            };

            // Draw wireframe sphere
            ctx.lineWidth = 0.5;
            for (const line of sphereLines) {
                ctx.beginPath();
                for (let i = 0; i < line.length; i++) {
                    const p = project(line[i].x, line[i].y, line[i].z);
                    if (i === 0) ctx.moveTo(p.px, p.py);
                    else ctx.lineTo(p.px, p.py);
                }
                ctx.strokeStyle = "rgba(0, 251, 251, 0.06)";
                ctx.stroke();
            }

            // Draw particles
            for (const particle of particles) {
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.z += particle.vz;

                // Wrap around
                if (Math.abs(particle.x) > 8) particle.vx *= -1;
                if (Math.abs(particle.y) > 8) particle.vy *= -1;
                if (Math.abs(particle.z) > 8) particle.vz *= -1;

                const p = project(particle.x, particle.y, particle.z);
                const size = 1.2 * p.perspective;
                const alpha = Math.max(0.1, 0.4 + p.depth * 0.05);

                ctx.beginPath();
                ctx.arc(p.px, p.py, size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0, 251, 251, ${alpha})`;
                ctx.fill();
            }

            rotY += 0.003;
            rotX += 0.001;
            floatOffset += 0.015;

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
    }, []);

    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
        </div>
    );
}

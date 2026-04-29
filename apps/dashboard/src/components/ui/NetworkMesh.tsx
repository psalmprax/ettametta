"use client";

import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { useMemo } from 'react';

interface Node extends d3.SimulationNodeDatum {
    id: string;
    group: number;
    label: string;
}

interface Link extends d3.SimulationLinkDatum<Node> {
    value: number;
}

interface NetworkProps {
    nodes: Node[];
    links: Link[];
}

interface SimNode extends d3.SimulationNodeDatum {
    id: string;
    group: number;
    label: string;
    x?: number;
    y?: number;
    vx?: number;
    vy?: number;
    fx?: number | null;
    fy?: number | null;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
    source: SimNode | string;
    target: SimNode | string;
    value: number;
}

export default React.memo(function NetworkMesh({ nodes, links }: NetworkProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

    // Handle resize
    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                const { width, height } = containerRef.current.getBoundingClientRect();
                setDimensions({
                    width: Math.floor(width),
                    height: Math.floor(height) || 500
                });
            }
        };

        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    // Remove unused memo and simplify - the simulation is created in renderNetwork
    const renderNetwork = useCallback(() => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const { width, height } = dimensions;

        // Clear only if needed or just update
        svg.selectAll("*").remove();

        // Create simulation with current dimensions
        const simNodes: SimNode[] = nodes.map(n => ({ 
            id: n.id, 
            group: n.group, 
            label: n.label,
            x: width / 2,
            y: height / 2
        }));
        
        const simLinks: SimLink[] = links.map(l => {
            const sourceId = typeof l.source === "string" ? l.source : l.source.id;
            const targetId = typeof l.target === "string" ? l.target : l.target.id;

            return {
                source: simNodes.find(n => n.id === sourceId) ?? sourceId,
                target: simNodes.find(n => n.id === targetId) ?? targetId,
                value: l.value
            };
        });

        const sim = d3.forceSimulation(simNodes)
            .force("link", d3.forceLink<SimNode, SimLink>(simLinks).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2));

        // Links
        const link = svg.append("g")
            .attr("stroke", "rgba(255,255,255,0.05)")
            .attr("stroke-width", 1.5)
            .selectAll("line")
            .data(simLinks)
            .enter().append("line");

        // Nodes group
        const node = svg.append("g")
            .selectAll<SVGGElement, SimNode>("g")
            .data(simNodes)
            .enter().append("g")
            .call(d3.drag<SVGGElement, SimNode>()
                .on("start", (event, d) => {
                    if (!event.active) sim.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on("drag", (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on("end", (event, d) => {
                    if (!event.active) sim.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }) as unknown as (selection: d3.Selection<SVGGElement, SimNode, SVGGElement, unknown>, ...args: unknown[]) => void);

        // Node circles
        node.append("circle")
            .attr("r", 8)
            .attr("fill", d => d.group === 1 ? "hsl(var(--primary))" : "#18181b")
            .attr("stroke", "rgba(255,255,255,0.1)")
            .attr("stroke-width", 2)
            .attr("filter", d => d.group === 1 ? "drop-shadow(0 0 10px rgba(var(--primary-rgb), 0.5))" : "none");

        // Node labels
        node.append("text")
            .attr("dx", 12)
            .attr("dy", ".35em")
            .text(d => d.label)
            .attr("fill", "rgba(255,255,255,0.4)")
            .attr("font-size", "10px")
            .attr("font-weight", "black")
            .attr("text-transform", "uppercase");

        // Tick function
        sim.on("tick", () => {
            link
                .attr("x1", d => typeof d.source === "string" ? 0 : d.source.x ?? 0)
                .attr("y1", d => typeof d.source === "string" ? 0 : d.source.y ?? 0)
                .attr("x2", d => typeof d.target === "string" ? 0 : d.target.x ?? 0)
                .attr("y2", d => typeof d.target === "string" ? 0 : d.target.y ?? 0);

            node.attr("transform", d => `translate(${d.x ?? 0},${d.y ?? 0})`);
        });

        return () => {
            sim.stop();
        };
    }, [nodes, links, dimensions]);

    useEffect(() => {
        const cleanup = renderNetwork();
        return () => {
            if (cleanup) cleanup();
        };
    }, [renderNetwork]);

    return (
        <div
            ref={containerRef}
            className="w-full h-[500px] bg-zinc-950/20 border border-white/5 rounded-[3rem] relative overflow-hidden"
            role="img"
            aria-label={`Network hierarchy visualization with ${nodes.length} nodes`}
        >
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            <svg
                ref={svgRef}
                width="100%"
                height="100%"
                viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
                aria-hidden="true"
            />
            <div className="absolute top-10 left-12 flex items-center gap-4">
                <div
                    className="h-2 w-2 rounded-full bg-primary animate-pulse"
                    aria-hidden="true"
                />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">
                    Network Hierarchy Simulation
                </span>
            </div>
        </div>
    );
});

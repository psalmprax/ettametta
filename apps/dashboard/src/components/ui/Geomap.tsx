"use client";

import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';

interface GeoData {
    type: string;
    features: GeoJSON.Feature[];
}

interface Point {
    lat: number;
    lng: number;
    intensity: number;
    label: string;
}

interface GeomapProps {
    points?: Point[];
}

export default React.memo(function Geomap({ points = [] }: GeomapProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 450 });

    // Handle resize
    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                const { width } = containerRef.current.getBoundingClientRect();
                setDimensions({
                    width: Math.min(width, 800),
                    height: Math.min(width * 0.56, 450)
                });
            }
        };

        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    const renderMap = useCallback(async () => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const { width, height } = dimensions;

        svg.selectAll("*").remove();
        setError(null);

        try {
            // Projection: Orthographic for that "Elite Global" feel
            const projection = d3.geoOrthographic()
                .scale(Math.min(width, height) / 2.5)
                .translate([width / 2, height / 2])
                .rotate([0, -20]);

            const pathGenerator = d3.geoPath().projection(projection);

            // Background Sphere
            svg.append("circle")
                .attr("cx", width / 2)
                .attr("cy", height / 2)
                .attr("r", projection.scale())
                .attr("fill", "rgba(0,0,0,0.5)")
                .attr("stroke", "rgba(255,255,255,0.05)")
                .attr("stroke-width", 1);

            // Fetch World Data
            const worldData = await d3.json<GeoData>(
                "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
            );

            if (!worldData) {
                throw new Error("Failed to load map data");
            }

            // Parse TopoJSON
            // @ts-ignore - topojson types can be tricky, trusting the library here
            const countries = topojson.feature(worldData as any, worldData.objects.countries as any) as unknown as GeoJSON.FeatureCollection;

            // Graticule
            const graticule = d3.geoGraticule();
            svg.append("path")
                .datum(graticule)
                .attr("class", "graticule")
                .attr("d", pathGenerator as unknown as string)
                .attr("fill", "none")
                .attr("stroke", "rgba(255,255,255,0.05)")
                .attr("stroke-width", 0.5);

            // Countries
            svg.selectAll<SVGPathElement, GeoJSON.Feature>(".country")
                .data(countries.features)
                .enter()
                .append("path")
                .attr("class", "country")
                .attr("d", pathGenerator)
                .attr("fill", "rgba(255,255,255,0.02)")
                .attr("stroke", "rgba(255,255,255,0.1)")
                .attr("stroke-width", 0.5)
                .on("mouseover", function () {
                    d3.select(this).attr("fill", "rgba(0, 242, 255, 0.1)");
                })
                .on("mouseout", function () {
                    d3.select(this).attr("fill", "rgba(255,255,255,0.02)");
                });

            // Pulse Points
            const pulseGroups = svg.selectAll<SVGGElement, Point>(".pulse")
                .data(points)
                .enter()
                .append("g")
                .attr("class", "pulse");

            pulseGroups.append("circle")
                .attr("class", "pulse-core")
                .attr("cx", d => {
                    const coords = projection([d.lng, d.lat]);
                    return coords ? coords[0] : 0;
                })
                .attr("cy", d => {
                    const coords = projection([d.lng, d.lat]);
                    return coords ? coords[1] : 0;
                })
                .attr("r", d => 2 + d.intensity * 5)
                .attr("fill", "#00f2ff")
                .attr("filter", "drop-shadow(0 0 5px #00f2ff)");

            pulseGroups.append("circle")
                .attr("class", "pulse-ring")
                .attr("cx", d => {
                    const coords = projection([d.lng, d.lat]);
                    return coords ? coords[0] : 0;
                })
                .attr("cy", d => {
                    const coords = projection([d.lng, d.lat]);
                    return coords ? coords[1] : 0;
                })
                .attr("r", 0)
                .attr("fill", "none")
                .attr("stroke", "#00f2ff")
                .attr("stroke-width", 1)
                .transition()
                .duration(2000)
                .delay((_d, i) => i * 200)
                .attr("r", 20)
                .attr("opacity", 0)
                .on("end", function repeat() {
                    d3.select(this)
                        .attr("r", 0)
                        .attr("opacity", 1)
                        .transition()
                        .duration(2000)
                        .attr("r", 20)
                        .attr("opacity", 0)
                        .on("end", repeat);
                });

            // Rotation Animation
            const timer = d3.timer((elapsed) => {
                projection.rotate([elapsed * 0.01, -20]);

                svg.selectAll<SVGPathElement, unknown>("path.country, path.graticule")
                    .attr("d", pathGenerator as unknown as string);

                svg.selectAll<SVGCircleElement, Point>("circle.pulse-core")
                    .attr("cx", d => {
                        const coords = projection([d.lng, d.lat]);
                        return coords ? coords[0] : 0;
                    })
                    .attr("cy", d => {
                        const coords = projection([d.lng, d.lat]);
                        return coords ? coords[1] : 0;
                    });

                svg.selectAll<SVGCircleElement, Point>("circle.pulse-ring")
                    .attr("cx", d => {
                        const coords = projection([d.lng, d.lat]);
                        return coords ? coords[0] : 0;
                    })
                    .attr("cy", d => {
                        const coords = projection([d.lng, d.lat]);
                        return coords ? coords[1] : 0;
                    });
            });

            setIsLoading(false);
            return () => timer.stop();

        } catch (err) {
            console.error("Geomap error:", err);
            setError(err instanceof Error ? err.message : "Failed to load map");
            setIsLoading(false);
        }
    }, [points, dimensions]);

    useEffect(() => {
        renderMap();
    }, [renderMap]);

    return (
        <div
            ref={containerRef}
            className="w-full flex justify-center py-10 overflow-hidden bg-zinc-950/20 rounded-[3rem] border border-white/5 relative"
            role="img"
            aria-label={`Global activity map showing ${points.length} active locations`}
        >
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary" />
                </div>
            )}

            {error && (
                <div className="absolute inset-0 flex items-center justify-center bg-zinc-950/80">
                    <div className="text-center p-4">
                        <p className="text-red-400 text-sm">{error}</p>
                        <button
                            onClick={() => { setIsLoading(true); renderMap(); }}
                            className="mt-2 px-4 py-2 bg-primary/20 text-primary text-xs uppercase tracking-wider rounded"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            )}

            <svg
                ref={svgRef}
                width={dimensions.width}
                height={dimensions.height}
                viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
                className="max-w-full h-auto"
                aria-hidden="true"
            />

            <div className="absolute bottom-10 left-12 space-y-1">
                <p className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.3em]">Neural Propagation</p>
                <p className="text-sm font-bold text-white uppercase italic">Active Nodes: {points.length}</p>
            </div>
        </div>
    );
});

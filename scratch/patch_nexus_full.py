#!/usr/bin/env python3
"""Comprehensive patch: DAG layout helpers + drag-and-drop repositioning.
Applied to clean stage HEAD of nexus/page.tsx."""

path = "apps/dashboard/src/app/nexus/page.tsx"
with open(path) as f:
    content = f.read()

original = content

# ============================================================
# 1. Add helpers + drag state before "    return (\n        <CommandCenterLayout"
# ============================================================
m1 = "    }, [actionLogs, systemLogs]);\n\n    return (\n        <CommandCenterLayout"

helpers_and_drag = '''    }, [actionLogs, systemLogs]);

    // ── DAG Layout Helpers ──────────────────────────────────────
    const DEFAULT_CINEMA_NODES = useMemo(() => [
        { type: "ingress", label: "Deep Discovery", desc: "Scanning viral clusters across platforms." },
        { type: "cognition", label: "Viral DNA Match", desc: "AI analysis of trending patterns." },
        { type: "synthesis", label: "Neural Remix", desc: "Applying cinematic overlays with Remotion." },
        { type: "egress", label: "Global Sync", desc: "Multi-platform publishing dispatch." },
    ], []);

    const dagNodes = useMemo(() => {
        const nodes = activeBlueprint?.nodes;
        if (nodes && nodes.length > 0) return nodes;
        return creationMode === "cinema" ? DEFAULT_CINEMA_NODES : [];
    }, [activeBlueprint, creationMode, DEFAULT_CINEMA_NODES]);

    const getDagCoords = useCallback((idx: number, total: number) => {
        if (total <= 1) return { x: 50, y: 50 };
        if (total === 2) return idx === 0 ? { x: 20, y: 35 } : { x: 75, y: 65 };
        if (total === 3) {
            const positions = [{ x: 12, y: 45 }, { x: 50, y: 30 }, { x: 88, y: 55 }];
            return positions[idx];
        }
        if (idx === 0) return { x: 10, y: 50 };
        if (idx === total - 1) return { x: 85, y: 50 };
        const mid = total - 2;
        const mi = idx - 1;
        const x = mid === 1 ? 45 : 30 + (mi / (mid - 1)) * 40;
        const y = mi % 2 === 0 ? 25 : 75;
        return { x, y };
    }, []);

    const getDagParents = useCallback((idx: number, total: number) => {
        if (idx === 0) return [] as number[];
        if (total <= 3) return [idx - 1];
        if (idx === 1 || idx === 2) return [0];
        if (idx === 3) return [1, 2];
        return [idx - 1];
    }, []);

    // ── Drag-and-Drop State ─────────────────────────────────
    const dagCanvasRef = useRef<HTMLDivElement>(null);
    const [draggedOffsets, setDraggedOffsets] = useState<Record<number, { x: number; y: number }>>({});

    const getAdjustedCoords = useCallback((idx: number, total: number) => {
        const base = getDagCoords(idx, total);
        const offset = draggedOffsets[idx];
        if (!offset) return base;
        return { x: base.x + offset.x, y: base.y + offset.y };
    }, [getDagCoords, draggedOffsets]);

    const handleNodeDrag = useCallback((_idx: number, info: { delta: { x: number; y: number } }) => {
        const canvas = dagCanvasRef.current;
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const dxPct = (info.delta.x / rect.width) * 100;
        const dyPct = (info.delta.y / rect.height) * 100;
        setDraggedOffsets(prev => {
            const current = prev[_idx] || { x: 0, y: 0 };
            return { ...prev, [_idx]: { x: current.x + dxPct, y: current.y + dyPct } };
        });
    }, []);

    const resetLayout = useCallback(() => {
        setDraggedOffsets({});
    }, []);

    const hasDraggedNodes = Object.keys(draggedOffsets).length > 0;

    return (
        <CommandCenterLayout'''

assert m1 in content, "Anchor 1 not found"
content = content.replace(m1, helpers_and_drag, 1)
print("OK 1/6: Added DAG helpers + drag state")

# ============================================================
# 2. Add canvas ref to DAG container
# ============================================================
m2 = '                                <div className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">'
r2 = '                                <div ref={dagCanvasRef} className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">'
assert m2 in content, "Anchor 2 not found"
content = content.replace(m2, r2, 1)
print("OK 2/6: Added canvas ref")

# ============================================================
# 3. Add DAG toolbar with Reset Layout button
# ============================================================
m3 = '                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">\n                                    {/* Neural Target Selector'
r3 = '''                                <div className="flex items-center justify-between shrink-0 mb-2">
                                    <div className="flex items-center gap-3">
                                        <div className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
                                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">DAG Pipeline</span>
                                        {hasDraggedNodes && (
                                            <button
                                                onClick={resetLayout}
                                                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[8px] font-bold uppercase tracking-widest hover:bg-amber-500/20 transition-all"
                                            >
                                                <RefreshCw className="h-2.5 w-2.5" /> Reset Layout
                                            </button>
                                        )}
                                    </div>
                                    <span className="text-[8px] text-zinc-600 font-mono uppercase tracking-tighter">Drag nodes to reposition</span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
                                    {/* Neural Target Selector'''
assert m3 in content, "Anchor 3 not found"
content = content.replace(m3, r3, 1)
print("OK 3/6: Added DAG toolbar with Reset button")

# ============================================================
# 4. Replace SVG connections section
# ============================================================
m4_start = '{/* Generate connections based on parallel branch coordinates */}\n                                            {activeBlueprint?.nodes?.map((node, idx) => {\n                                                if (idx === 0) return null;\n                                                const listLength = activeBlueprint?.nodes?.length || 0;'
assert m4_start in content, "Anchor 4a not found"
content = content.replace(m4_start,
    '{/* Generate connections using shared DAG layout */}\n                                            {dagNodes.map((node, idx) => {\n                                                const total = dagNodes.length;\n                                                const parentIndices = getDagParents(idx, total);\n                                                if (parentIndices.length === 0) return null;', 1)
print("OK 4a: Replaced SVG map header")

# Remove old getCoords + parentIndices block
m4b = '''                                                // Dynamic Coordinates logic
                                                const getCoords = (i: number) => {
                                                    let x = 15 + (i / Math.max(listLength - 1, 1)) * 70;
                                                    let y = 50;
                                                    if (listLength >= 4) {
                                                        if (i === 0) { x = 15; y = 50; }
                                                        else if (i === 1) { x = 45; y = 25; } // Branch 1: Script Cognition
                                                        else if (i === 2) { x = 45; y = 75; } // Branch 2: Asset Discovery
                                                        else if (i === 3) { x = 75; y = 50; } // Merge: Synthesis
                                                        else if (i >= 4) { x = 90; y = 50; }
                                                    }
                                                    return { x, y };
                                                };
                                                
                                                let parentIndices = [idx - 1];
                                                if (listLength >= 4) {
                                                    if (idx === 1) parentIndices = [0];
                                                    if (idx === 2) parentIndices = [0];
                                                    if (idx === 3) parentIndices = [1, 2]; // Merge node
                                                    if (idx === 4) parentIndices = [3];
                                                }
                                                
                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getCoords(parentIdx);
                                                    const end = getCoords(idx);'''
assert m4b in content, "Anchor 4b not found"
content = content.replace(m4b, '''                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getAdjustedCoords(parentIdx, total);
                                                    const end = getAdjustedCoords(idx, total);''', 1)
print("OK 4b: Replaced SVG coords with shared helpers")

# Add animated particle before closing </g>
m4c = '''                                                        </g>
                                                    );
                                                });
                                            })}'''
assert m4c in content, "Anchor 4c not found"
content = content.replace(m4c, '''                                                        {isPathActive && (
                                                            <circle r="1.5" fill="#22d3ee" opacity="0.9" filter="url(#glowFilter)">
                                                                <animateMotion dur="2s" repeatCount="indefinite" path={pathD} />
                                                            </circle>
                                                        )}
                                                        </g>
                                                    );
                                                });
                                            })}''', 1)
print("OK 4c: Added animated flow particles")

# ============================================================
# 5. Replace node positioning with drag-enabled motion.div
# ============================================================
m5 = '''                                    {/* Position Nodes based on branch coordinates */}
                                    <div className="absolute inset-0 z-10">
                                        {activeBlueprint?.nodes?.map((node, idx) => {
                                            const isProcessing = activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                                            const isComplete = activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                                            const listLength = activeBlueprint?.nodes?.length || 0;
                                            
                                            let x = 15 + (idx / Math.max(listLength - 1, 1)) * 70;
                                            let y = 50;
                                            if (listLength >= 4) {
                                                if (idx === 0) { x = 15; y = 50; }
                                                else if (idx === 1) { x = 45; y = 25; }
                                                else if (idx === 2) { x = 45; y = 75; }
                                                else if (idx === 3) { x = 75; y = 50; }
                                                else if (idx >= 4) { x = 90; y = 50; }
                                            }
                                            
                                            return (
                                                <div 
                                                    key={idx} 
                                                    className="absolute"
                                                    style={{ 
                                                        left: `${x}%`, 
                                                        top: `${y}%`, 
                                                        transform: 'translate(-50%, -50%)' 
                                                    }}
                                                >
                                                    <NexusNode 
                                                        type={node.type as any}
                                                        label={node.label}
                                                        description={node.desc}
                                                        status={isComplete ? "complete" : isProcessing ? "processing" : "pending"}
                                                        progress={isProcessing ? activePipelineJob.progress : undefined}
                                                        active={selectedNodeIndex === idx}
                                                        onClick={() => setSelectedNodeIndex(idx)}
                                                    />
                                                </div>
                                            );
                                        })}
                                    </div>'''
assert m5 in content, "Anchor 5 not found"
content = content.replace(m5, '''                                    {/* Position Nodes — drag-enabled DAG layout */}
                                    <div className="absolute inset-0 z-10">
                                        {dagNodes.map((node, idx) => {
                                            const total = dagNodes.length;
                                            const { x, y } = getAdjustedCoords(idx, total);
                                            const isProcessing = activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                                            const isComplete = activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                                            const isDragged = !!draggedOffsets[idx];
                                            
                                            return (
                                                <motion.div 
                                                    key={idx} 
                                                    className="absolute cursor-grab active:cursor-grabbing"
                                                    drag
                                                    dragMomentum={false}
                                                    dragElastic={0}
                                                    onDrag={(_, info) => handleNodeDrag(idx, info)}
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ 
                                                        opacity: 1, 
                                                        scale: 1,
                                                        left: `${x}%`,
                                                        top: `${y}%`,
                                                    }}
                                                    transition={{ 
                                                        opacity: { delay: idx * 0.12, duration: 0.4 },
                                                        scale: { delay: idx * 0.12, duration: 0.4 },
                                                        left: { type: "spring", stiffness: 300, damping: 30 },
                                                        top: { type: "spring", stiffness: 300, damping: 30 },
                                                    }}
                                                    style={{ transform: 'translate(-50%, -50%)' }}
                                                >
                                                    <div className={cn(
                                                        "transition-shadow duration-300",
                                                        isDragged && "ring-1 ring-cyan-500/30 rounded-4xl shadow-[0_0_20px_rgba(34,211,238,0.15)]"
                                                    )}>
                                                        <NexusNode 
                                                            type={node.type as any}
                                                            label={node.label}
                                                            description={node.desc}
                                                            status={isComplete ? "complete" : isProcessing ? "processing" : "pending"}
                                                            progress={isProcessing ? activePipelineJob?.progress : undefined}
                                                            active={selectedNodeIndex === idx}
                                                            onClick={() => setSelectedNodeIndex(idx)}
                                                        />
                                                    </div>
                                                </motion.div>
                                            );
                                        })}
                                    </div>''', 1)
print("OK 5/6: Replaced node positioning with drag-enabled motion.div")

# ============================================================
# 6. Verify no stale references remain
# ============================================================
assert "activeBlueprint?.nodes?.map" not in content, "Old activeBlueprint map still present!"
assert "getAdjustedCoords" in content, "getAdjustedCoords not found!"
assert "dagCanvasRef" in content, "dagCanvasRef not found!"
assert "draggedOffsets" in content, "draggedOffsets not found!"
assert "handleNodeDrag" in content, "handleNodeDrag not found!"
assert "drag\n" in content or "drag " in content, "drag prop not found on motion.div!"
assert "dragMomentum={false}" in content, "dragMomentum not found!"
assert "resetLayout" in content, "resetLayout not found!"
print("OK 6/6: All verifications passed")

with open(path, "w") as f:
    f.write(content)

print(f"\n✅ Comprehensive patch applied. {len(original)} -> {len(content)} chars ({len(content) - len(original):+d})")

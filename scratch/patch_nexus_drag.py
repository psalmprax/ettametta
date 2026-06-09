#!/usr/bin/env python3
"""Add interactive drag-and-drop node repositioning to the DAG canvas."""

path = "apps/dashboard/src/app/nexus/page.tsx"
with open(path) as f:
    content = f.read()

original_len = len(content)

# ============================================================
# 1. Add drag state, canvas ref, and helper after getDagParents
# ============================================================
anchor1 = '''    const getDagParents = useCallback((idx: number, total: number) => {
        if (idx === 0) return [] as number[];
        if (total <= 3) return [idx - 1];
        if (idx === 1 || idx === 2) return [0];
        if (idx === 3) return [1, 2];
        return [idx - 1];
    }, []);

    return ('''

replacement1 = '''    const getDagParents = useCallback((idx: number, total: number) => {
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

    const handleNodeDrag = useCallback((idx: number, info: { delta: { x: number; y: number } }) => {
        const canvas = dagCanvasRef.current;
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const dxPct = (info.delta.x / rect.width) * 100;
        const dyPct = (info.delta.y / rect.height) * 100;
        setDraggedOffsets(prev => {
            const current = prev[idx] || { x: 0, y: 0 };
            return { ...prev, [idx]: { x: current.x + dxPct, y: current.y + dyPct } };
        });
    }, []);

    const resetLayout = useCallback(() => {
        setDraggedOffsets({});
    }, []);

    const hasDraggedNodes = Object.keys(draggedOffsets).length > 0;

    return ('''

assert anchor1 in content, "Anchor 1 (getDagParents + return) not found"
content = content.replace(anchor1, replacement1, 1)
print("OK: Added drag state, canvas ref, helpers")

# ============================================================
# 2. Modify SVG connections to use getAdjustedCoords
# ============================================================
anchor2 = '''                                                    const start = getDagCoords(parentIdx, total);
                                                    const end = getDagCoords(idx, total);'''

replacement2 = '''                                                    const start = getAdjustedCoords(parentIdx, total);
                                                    const end = getAdjustedCoords(idx, total);'''

assert anchor2 in content, "Anchor 2 (SVG getDagCoords calls) not found"
content = content.replace(anchor2, replacement2, 1)
print("OK: SVG paths now use adjusted (draggable) coordinates")

# ============================================================
# 3. Add canvas ref to the DAG container div
# ============================================================
anchor3 = '''                                <div className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">'''

replacement3 = '''                                <div ref={dagCanvasRef} className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">'''

assert anchor3 in content, "Anchor 3 (DAG canvas container div) not found"
content = content.replace(anchor3, replacement3, 1)
print("OK: Added canvas ref to DAG container")

# ============================================================
# 4. Add Reset Layout button to the orchestrator toolbar area
# ============================================================
anchor4 = '''                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">'''

replacement4 = '''                                <div className="flex items-center justify-between shrink-0">
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
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">'''

assert anchor4 in content, "Anchor 4 (grid cols start) not found"
content = content.replace(anchor4, replacement4, 1)
print("OK: Added DAG toolbar with Reset Layout button")

# ============================================================
# 5. Replace node positioning with drag-enabled motion.div
# ============================================================
anchor5 = '''                                    {/* Position Nodes using shared DAG layout */}
                                    <div className="absolute inset-0 z-10">
                                        {dagNodes.map((node, idx) => {
                                            const total = dagNodes.length;
                                            const { x, y } = getDagCoords(idx, total);
                                            const isProcessing = activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                                            const isComplete = activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                                            
                                            return (
                                                <motion.div 
                                                    key={idx} 
                                                    className="absolute"
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    transition={{ delay: idx * 0.12, duration: 0.4 }}
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
                                                        progress={isProcessing ? activePipelineJob?.progress : undefined}
                                                        active={selectedNodeIndex === idx}
                                                        onClick={() => setSelectedNodeIndex(idx)}
                                                    />
                                                </motion.div>
                                            );
                                        })}
                                    </div>'''

replacement5 = '''                                    {/* Position Nodes using shared DAG layout + drag */}
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
                                    </div>'''

assert anchor5 in content, "Anchor 5 (node positioning section) not found"
content = content.replace(anchor5, replacement5, 1)
print("OK: Added drag props to node positioning")

# ============================================================
# 6. Also fix the SVG section to use getAdjustedCoords for start/end
# ============================================================
# Already done in step 2. Verify there are no remaining getDagCoords calls in SVG.
svg_section_start = content.find("{/* Generate connections using shared DAG layout */}")
svg_section_end = content.find("{/* Position Nodes", svg_section_start)
svg_section = content[svg_section_start:svg_section_end]
assert "getDagCoords" not in svg_section, "SVG section still has getDagCoords (should be getAdjustedCoords)"
print("OK: Verified SVG section uses getAdjustedCoords")

# Write result
with open(path, "w") as f:
    f.write(content)

print(f"\nAll drag-and-drop patches applied. {original_len} -> {len(content)} chars")

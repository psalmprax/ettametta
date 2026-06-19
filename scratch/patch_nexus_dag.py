#!/usr/bin/env python3
"""Apply DAG layout improvements to nexus/page.tsx"""
import sys

path = "apps/dashboard/src/app/nexus/page.tsx"
with open(path) as f:
    content = f.read()

original = content

# ============================================================
# 1. Add helpers before "    return (\n        <CommandCenterLayout"
# ============================================================
helpers = '''
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

'''

m1 = "    }, [actionLogs, systemLogs]);\n\n    return (\n        <CommandCenterLayout"
assert m1 in content, f"Marker 1 not found"
content = content.replace(m1, "    }, [actionLogs, systemLogs]);\n" + helpers + "\n    return (\n        <CommandCenterLayout", 1)
print("✓ Added DAG helpers")

# ============================================================
# 2. Replace SVG connection section header
# ============================================================
m2 = '{/* Generate connections based on parallel branch coordinates */}\n                                    {activeBlueprint?.nodes?.map((node, idx) => {'
assert m2 in content, "Marker 2 not found"
content = content.replace(m2, '{/* Generate connections using shared DAG layout */}\n                                    {dagNodes.map((node, idx) => {', 1)
print("✓ Replaced SVG map header")

# ============================================================
# 3. Replace getCoords + parentIndices block
# ============================================================
m3 = '''                                                if (idx === 0) return null;
                                                const listLength = activeBlueprint?.nodes?.length || 0;
                                                
                                                // Dynamic Coordinates logic
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
                                                }'''
assert m3 in content, "Marker 3 not found"
content = content.replace(m3, '''                                                const total = dagNodes.length;
                                                const parentIndices = getDagParents(idx, total);
                                                if (parentIndices.length === 0) return null;''', 1)
print("✓ Replaced SVG coords logic")

# ============================================================
# 4. Replace getCoords calls with getDagCoords
# ============================================================
m4 = '''                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getCoords(parentIdx);
                                                    const end = getCoords(idx);'''
assert m4 in content, "Marker 4 not found"
content = content.replace(m4, '''                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getDagCoords(parentIdx, total);
                                                    const end = getDagCoords(idx, total);''', 1)
print("✓ Replaced SVG getCoords calls")

# ============================================================
# 5. Add animated flow particle before closing </g>
# ============================================================
m5 = '''                                                        </g>
                                                    );
                                                });
                                            })}'''
assert m5 in content, "Marker 5 not found"
content = content.replace(m5, '''                                                        {isPathActive && (
                                                            <circle r="1.5" fill="#22d3ee" opacity="0.9" filter="url(#glowFilter)">
                                                                <animateMotion dur="2s" repeatCount="indefinite" path={pathD} />
                                                            </circle>
                                                        )}
                                                        </g>
                                                    );
                                                });
                                            })}''', 1)
print("✓ Added animated flow particles")

# ============================================================
# 6. Replace node positioning section
# ============================================================
m6 = '''                                    {/* Position Nodes based on branch coordinates */}
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
assert m6 in content, "Marker 6 not found"
content = content.replace(m6, '''                                    {/* Position Nodes using shared DAG layout */}
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
                                    </div>''', 1)
print("✓ Replaced node positioning with motion.div + shared helpers")

# Write result
with open(path, "w") as f:
    f.write(content)

print(f"\n✅ All patches applied. {len(original)} -> {len(content)} chars")

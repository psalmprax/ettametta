#!/usr/bin/env python3
"""Apply markers 2-6 (SVG + node positioning) to nexus/page.tsx.
Marker 1 (helpers) was already applied. This uses 44-space indentation."""

path = "apps/dashboard/src/app/nexus/page.tsx"
with open(path) as f:
    content = f.read()

# 2. Replace SVG map header
m2 = '{/* Generate connections based on parallel branch coordinates */}\n                                            {activeBlueprint?.nodes?.map((node, idx) => {'
assert m2 in content, "Marker 2 not found"
content = content.replace(m2, '{/* Generate connections using shared DAG layout */}\n                                            {dagNodes.map((node, idx) => {', 1)
print("OK marker 2")

# 3. Replace getCoords + parentIndices block (44-space indent)
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
print("OK marker 3")

# 4. Replace getCoords calls
m4 = '''                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getCoords(parentIdx);
                                                    const end = getCoords(idx);'''
assert m4 in content, "Marker 4 not found"
content = content.replace(m4, '''                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getDagCoords(parentIdx, total);
                                                    const end = getDagCoords(idx, total);''', 1)
print("OK marker 4")

# 5. Add animated flow particle
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
print("OK marker 5")

# 6. Replace node positioning section
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
print("OK marker 6")

with open(path, "w") as f:
    f.write(content)
print(f"All markers 2-6 applied. File: {len(content)} chars")

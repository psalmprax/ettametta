"use client";

import React, { useRef, useMemo, useLayoutEffect, useState, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float, Stars, PerspectiveCamera, MeshTransmissionMaterial } from '@react-three/drei';
import * as THREE from 'three';

type WebglState = 'loading' | 'supported' | 'unsupported';

function GlobeFallback() {
    return (
        <div className="h-[600px] w-full relative flex items-center justify-center bg-zinc-950/30 rounded-lg">
            <div className="text-center space-y-2">
                <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 animate-pulse" />
                <p className="text-zinc-400 text-sm">Neural Globe</p>
            </div>
        </div>
    );
}

function GlobalPulseGlobeInner({ pulseIntensity }: { pulseIntensity?: number }) {
    const [webglState, setWebglState] = useState<WebglState>('loading');

    useEffect(() => {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            setWebglState(gl ? 'supported' : 'unsupported');
        } catch {
            setWebglState('unsupported');
        }
    }, []);

    if (webglState !== 'supported') {
        return <GlobeFallback />;
    }

    return <Globe3DRenderer pulseIntensity={pulseIntensity} />;
}

// The actual Three.js rendering
function Globe3DRenderer({ pulseIntensity = 1 }: { pulseIntensity?: number }) {
    const groupRef = useRef<THREE.Group>(null);
    const geoRef = useRef<THREE.BufferGeometry>(null);
    const { mouse } = useThree();

    // Generate nodes and connections
    const { nodes, linePositions } = useMemo(() => {
        const nodeCount = 120;
        const pts: THREE.Vector3[] = [];
        for (let i = 0; i < nodeCount; i++) {
            const phi = Math.acos(-1 + (2 * i) / nodeCount);
            const theta = Math.sqrt(nodeCount * Math.PI) * phi;
            pts.push(new THREE.Vector3().setFromSphericalCoords(2.1, phi, theta));
        }

        const lines: number[] = [];
        const maxDist = 0.8;
        for (let i = 0; i < pts.length; i++) {
            let matches = 0;
            for (let j = i + 1; j < pts.length; j++) {
                if (pts[i].distanceTo(pts[j]) < maxDist && matches < 3) {
                    lines.push(pts[i].x, pts[i].y, pts[i].z, pts[j].x, pts[j].y, pts[j].z);
                    matches++;
                }
            }
        }
        return { nodes: pts, linePositions: new Float32Array(lines) };
    }, []);

    useLayoutEffect(() => {
        if (geoRef.current) {
            geoRef.current.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        }
    }, [linePositions]);

    useFrame((state) => {
        if (groupRef.current) {
            // Mouse Parallax
            groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, mouse.x * 0.4, 0.05);
            groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, -mouse.y * 0.4, 0.05);

            // Auto rotation base
            groupRef.current.rotation.y += 0.001;
            
            // Pulse reaction: Scale slightly based on intensity
            const scale = 1 + (pulseIntensity * 0.02);
            groupRef.current.scale.lerp(new THREE.Vector3(scale, scale, scale), 0.1);
        }
    });

    return (
        <group ref={groupRef}>
            {/* Core Neural Shell */}
            <Sphere args={[2, 64, 64]}>
                <MeshTransmissionMaterial
                    backside
                    samples={8}
                    thickness={1.2}
                    chromaticAberration={0.05}
                    anisotropy={0.2}
                    distortion={0.2}
                    distortionScale={0.1}
                    temporalDistortion={0.1}
                    color="#001a1a"
                    roughness={0}
                />
            </Sphere>

            {/* Glowing Nodes */}
            {nodes.map((pos, i) => (
                <mesh key={`node-${i}`} position={pos} scale={1 + pulseIntensity * 0.5}>
                    <sphereGeometry args={[0.015, 8, 8]} />
                    <meshBasicMaterial
                        color={i % 3 === 0 ? "#00f2ff" : "#10b981"}
                        transparent
                        opacity={0.3 + (pulseIntensity * 0.7)}
                    />
                </mesh>
            ))}

            {/* Neural Connections (Unified LineSegments) */}
            <lineSegments>
                <bufferGeometry ref={geoRef} />
                <lineBasicMaterial 
                    color="#00f2ff" 
                    transparent 
                    opacity={0.05 + (pulseIntensity * 0.4)} 
                />
            </lineSegments>

            <ambientLight intensity={0.2 + (pulseIntensity * 0.3)} />
            <pointLight position={[10, 10, 10]} intensity={1.5 + pulseIntensity} color="#00f2ff" />
            <pointLight position={[-10, -10, -10]} intensity={1 + pulseIntensity} color="#10b981" />
        </group>
    );
}


export default React.memo(function GlobalPulseGlobe({ pulseIntensity }: { pulseIntensity?: number }) {
    return <GlobalPulseGlobeInner pulseIntensity={pulseIntensity} />;
});

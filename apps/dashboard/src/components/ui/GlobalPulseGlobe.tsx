"use client";

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float, Stars, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

function Globe({ pulseIntensity = 1 }: { pulseIntensity?: number }) {
    const meshRef = useRef<THREE.Mesh>(null);
    const glowRef = useRef<THREE.Mesh>(null);

    useFrame((state) => {
        if (meshRef.current) {
            meshRef.current.rotation.y += 0.002;
            meshRef.current.rotation.x += 0.001;
        }
        if (glowRef.current) {
            glowRef.current.rotation.y -= 0.001;
            const s = 1.2 + Math.sin(state.clock.elapsedTime * 2) * 0.05 * pulseIntensity;
            glowRef.current.scale.set(s, s, s);
        }
    });

    const points = useMemo(() => {
        const p = [];
        for (let i = 0; i < 200; i++) {
            const phi = Math.acos(-1 + (2 * i) / 200);
            const theta = Math.sqrt(200 * Math.PI) * phi;
            p.push(new THREE.Vector3().setFromSphericalCoords(2.05, phi, theta));
        }
        return p;
    }, []);

    return (
        <group>
            {/* Core Sphere */}
            <Sphere ref={meshRef} args={[2, 64, 64]}>
                <MeshDistortMaterial
                    color="#000000"
                    speed={2}
                    distort={0.3}
                    roughness={0.1}
                    metalness={1}
                />
            </Sphere>

            {/* Neural Web (Points) */}
            <group>
                {points.map((pos, i) => (
                    <mesh key={i} position={pos}>
                        <sphereGeometry args={[0.02, 8, 8]} />
                        <meshBasicMaterial color="#00f2ff" />
                    </mesh>
                ))}
            </group>

            {/* Atmospheric Glow */}
            <Sphere ref={glowRef} args={[2.1, 64, 64]}>
                <meshBasicMaterial
                    color="#00f2ff"
                    transparent
                    opacity={0.05}
                    wireframe
                />
            </Sphere>

            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={1} color="#00f2ff" />
        </group>
    );
}

export default React.memo(function GlobalPulseGlobe({ pulseIntensity }: { pulseIntensity?: number }) {
    return (
        <div
            className="h-[400px] w-full relative pointer-events-none"
            role="img"
            aria-label="Animated 3D globe visualization showing global neural network activity"
        >
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-zinc-950 z-10" />
            <Canvas>
                <PerspectiveCamera makeDefault position={[0, 0, 8]} />
                <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                <Float speed={2} rotationIntensity={1} floatIntensity={1}>
                    <Globe pulseIntensity={pulseIntensity} />
                </Float>
            </Canvas>
        </div>
    );
});

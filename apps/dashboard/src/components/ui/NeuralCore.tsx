"use client";

import React, { useRef, useState, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial, Sphere, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";

function NeuralParticles() {
    const points = useRef<THREE.Points>(null!);
    const [particleCount] = useState(2000);
    const positions = React.useMemo(() => {
        const pos = new Float32Array(particleCount * 3);
        for (let i = 0; i < particleCount; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 15;
            pos[i * 3 + 1] = (Math.random() - 0.5) * 15;
            pos[i * 3 + 2] = (Math.random() - 0.5) * 15;
        }
        return pos;
    }, [particleCount]);

    useFrame((state) => {
        const time = state.clock.getElapsedTime();
        points.current.rotation.y = time * 0.05;
        points.current.rotation.x = time * 0.03;
    });

    return (
        <Points ref={points} positions={positions} stride={3}>
            <PointMaterial
                transparent
                color="#00fbfb"
                size={0.02}
                sizeAttenuation={true}
                depthWrite={false}
                blending={THREE.AdditiveBlending}
            />
        </Points>
    );
}

export default function NeuralCore() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
            <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#00fbfb" />
                    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
                        <Sphere args={[1, 64, 64]} scale={1.5}>
                            <MeshDistortMaterial
                                color="#00fbfb"
                                speed={4}
                                distort={0.4}
                                radius={1}
                                wireframe
                                transparent
                                opacity={0.15}
                            />
                        </Sphere>
                    </Float>
                    <NeuralParticles />
                </Suspense>
            </Canvas>
        </div>
    );
}

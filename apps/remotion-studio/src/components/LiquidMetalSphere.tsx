import React, { useRef } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Environment } from '@react-three/drei';
import * as THREE from 'three';

export const LiquidMetalSphere: React.FC<{ primaryColor: string }> = ({ primaryColor }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const sphereRef = useRef<THREE.Mesh>(null);

    // Dynamic morphing speed and rotation
    useFrame(() => {
        if (sphereRef.current) {
            sphereRef.current.rotation.x = frame * 0.01;
            sphereRef.current.rotation.y = frame * 0.02;
        }
    });

    return (
        <group>
            {/* Soft, rich lighting to bounce off the liquid metal */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 10, 5]} intensity={3} color="#ffffff" />
            <directionalLight position={[-10, -10, -5]} intensity={2} color={primaryColor} />
            <pointLight position={[0, 0, 10]} intensity={1.5} color={primaryColor} />

            <mesh ref={sphereRef} scale={2}>
                <sphereGeometry args={[1, 64, 64]} />
                <MeshDistortMaterial
                    color="#ffffff"
                    emissive={primaryColor}
                    emissiveIntensity={0.2}
                    metalness={1}
                    roughness={0.1}
                    clearcoat={1}
                    clearcoatRoughness={0.1}
                    distort={0.4}
                    speed={2}
                />
            </mesh>
        </group>
    );
};

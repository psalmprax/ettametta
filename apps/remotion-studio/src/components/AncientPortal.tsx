import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { Environment, Float, Sparkles, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

interface PortalProps {
    primaryColor?: string;
}

export const AncientPortal: React.FC<PortalProps> = ({ primaryColor = '#FF8C00' }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const portalCore = useRef<THREE.Mesh>(null);
    const outerRing1 = useRef<THREE.Mesh>(null);
    const outerRing2 = useRef<THREE.Mesh>(null);

    useFrame(() => {
        const time = frame / fps;
        
        if (outerRing1.current) {
            outerRing1.current.rotation.z = time * 0.5;
        }
        if (outerRing2.current) {
            outerRing2.current.rotation.z = time * -0.3;
        }
        if (portalCore.current) {
            portalCore.current.rotation.y = time * 0.1;
        }
    });

    // Highly emissive materials to act as light sources
    const runicMaterial = new THREE.MeshStandardMaterial({
        color: '#ffffff',
        emissive: new THREE.Color(primaryColor),
        emissiveIntensity: 4, // High bloom trigger
        roughness: 0.1,
        metalness: 1,
        wireframe: true, // Gives a complex geometric/runic look
    });

    return (
        <>
            <ambientLight intensity={0.5} />
            <pointLight position={[0, 0, 0]} intensity={100} color={primaryColor} distance={20} />
            <directionalLight position={[5, 5, 5]} intensity={1} color="#ffffff" />
            <directionalLight position={[-5, -5, -5]} intensity={0.5} color={primaryColor} />
            
            <Float speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
                <group position={[0, 0, -2]}>
                    
                    {/* The Energy Core (Distorted Sphere) */}
                    <mesh ref={portalCore}>
                        <sphereGeometry args={[1.5, 64, 64]} />
                        <MeshDistortMaterial 
                            color="#000000" 
                            emissive={primaryColor} 
                            emissiveIntensity={1}
                            distort={0.4} 
                            speed={3} 
                            roughness={0}
                        />
                    </mesh>

                    {/* Outer Runic Geometry 1 */}
                    <mesh ref={outerRing1}>
                        <torusGeometry args={[3, 0.1, 16, 100]} />
                        <primitive object={runicMaterial} attach="material" />
                    </mesh>
                    
                    {/* Outer Runic Geometry 2 */}
                    <mesh ref={outerRing2}>
                        <torusGeometry args={[3.5, 0.05, 8, 100]} />
                        <primitive object={runicMaterial} attach="material" />
                    </mesh>

                    {/* Magical floating dust/sparks */}
                    <Sparkles 
                        count={500} 
                        scale={8} 
                        size={2} 
                        speed={0.4} 
                        opacity={0.8} 
                        color={primaryColor} 
                    />
                </group>
            </Float>
        </>
    );
};

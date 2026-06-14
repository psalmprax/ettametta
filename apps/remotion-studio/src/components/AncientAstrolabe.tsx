import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { Environment, Float } from '@react-three/drei';
import * as THREE from 'three';

interface AstrolabeProps {
    primaryColor?: string;
}

export const AncientAstrolabe: React.FC<AstrolabeProps> = ({ primaryColor = '#FFD700' }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const ring1 = useRef<THREE.Mesh>(null);
    const ring2 = useRef<THREE.Mesh>(null);
    const ring3 = useRef<THREE.Mesh>(null);
    const group = useRef<THREE.Group>(null);

    // Dynamic rotation based on Remotion frame
    useFrame(() => {
        const time = frame / fps;
        
        if (ring1.current) {
            ring1.current.rotation.x = time * 0.5;
            ring1.current.rotation.y = time * 0.2;
        }
        if (ring2.current) {
            ring2.current.rotation.y = time * -0.4;
            ring2.current.rotation.z = time * 0.3;
        }
        if (ring3.current) {
            ring3.current.rotation.x = time * 0.3;
            ring3.current.rotation.z = time * -0.5;
        }
        if (group.current) {
            group.current.rotation.y = time * 0.1; // Slow overall rotation
        }
    });

    const glassMaterial = new THREE.MeshPhysicalMaterial({
        color: primaryColor,
        metalness: 0.9,
        roughness: 0.1,
        transmission: 0.9,
        ior: 1.5,
        thickness: 0.5,
        emissive: new THREE.Color(primaryColor),
        emissiveIntensity: 0.2,
        transparent: true,
        opacity: 0.9,
        side: THREE.DoubleSide
    });

    const coreMaterial = new THREE.MeshStandardMaterial({
        color: '#ffffff',
        emissive: new THREE.Color(primaryColor),
        emissiveIntensity: 2,
        roughness: 0.2,
        metalness: 1
    });

    return (
        <>
            <Environment preset="city" />
            
            <ambientLight intensity={0.5} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={100} color={primaryColor} />
            <spotLight position={[-10, -10, -10]} angle={0.15} penumbra={1} intensity={50} color="#ffffff" />
            
            <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
                <group ref={group}>
                    {/* Outer Ring */}
                    <mesh ref={ring1}>
                        <torusGeometry args={[4, 0.15, 16, 100]} />
                        <primitive object={glassMaterial} attach="material" />
                    </mesh>
                    
                    {/* Middle Ring */}
                    <mesh ref={ring2}>
                        <torusGeometry args={[3.2, 0.1, 16, 100]} />
                        <primitive object={glassMaterial} attach="material" />
                    </mesh>
                    
                    {/* Inner Ring */}
                    <mesh ref={ring3}>
                        <torusGeometry args={[2.5, 0.08, 16, 100]} />
                        <primitive object={glassMaterial} attach="material" />
                    </mesh>

                    {/* Glowing Core */}
                    <mesh>
                        <sphereGeometry args={[0.5, 32, 32]} />
                        <primitive object={coreMaterial} attach="material" />
                    </mesh>
                </group>
            </Float>
        </>
    );
};

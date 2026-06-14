import React, { useRef } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { useFrame } from '@react-three/fiber';
import { MeshTransmissionMaterial, Text } from '@react-three/drei';
import * as THREE from 'three';

export const ChromaticPrism: React.FC<{ primaryColor: string, title: string, subtitle: string }> = ({ primaryColor, title, subtitle }) => {
    const frame = useCurrentFrame();
    const prismRef = useRef<THREE.Mesh>(null);

    useFrame(() => {
        if (prismRef.current) {
            prismRef.current.rotation.x = frame * 0.005;
            prismRef.current.rotation.y = frame * 0.01;
            prismRef.current.rotation.z = frame * 0.002;
        }
    });

    return (
        <group>
            {/* Soft Ambient Light */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 10, 10]} intensity={2} color="#ffffff" />
            <pointLight position={[-10, -10, -10]} intensity={1.5} color={primaryColor} />

            {/* Background Typography to be refracted */}
            <group position={[0, 0, -5]}>
                <Text
                    fontSize={1.5}
                    fontWeight={200}
                    letterSpacing={0.2}
                    color="white"
                    anchorX="center"
                    anchorY="bottom"
                    position={[0, 0.2, 0]}
                >
                    {title}
                </Text>
                <Text
                    fontSize={0.5}
                    fontWeight={400}
                    letterSpacing={0.3}
                    color={primaryColor}
                    anchorX="center"
                    anchorY="top"
                    position={[0, -0.2, 0]}
                >
                    {subtitle}
                </Text>
            </group>

            {/* The refracting Prism in the foreground */}
            <mesh ref={prismRef} scale={3.5} position={[0, 0, 0]}>
                <icosahedronGeometry args={[1, 0]} />
                <MeshTransmissionMaterial
                    transmission={1}
                    thickness={1.5}
                    roughness={0.05}
                    ior={1.5}
                    chromaticAberration={0.06}
                    anisotropy={0.3}
                    clearcoat={1}
                    color="#ffffff"
                    distortion={0.5}
                    distortionScale={0.5}
                    temporalDistortion={0.1}
                />
            </mesh>
        </group>
    );
};

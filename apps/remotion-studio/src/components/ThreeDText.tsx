import React, { useRef } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { Text, Float, Environment, ContactShadows } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ThreeDTextProps {
    text: string;
    subtitle?: string;
    primaryColor?: string;
}

export const ThreeDText: React.FC<ThreeDTextProps> = ({ 
    text, 
    subtitle, 
    primaryColor = '#00F2FE' 
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const groupRef = useRef<THREE.Group>(null);
    const textRef = useRef<any>(null);

    // Slowly rotate the entire text group based on the frame
    useFrame(() => {
        if (groupRef.current) {
            // Gentle cinematic pan
            groupRef.current.rotation.y = Math.sin(frame / 120) * 0.15;
            groupRef.current.position.z = Math.sin(frame / 60) * 0.5;
        }
    });

    return (
        <group ref={groupRef}>
            {/* Environment provides cinematic studio lighting reflections */}
            <Environment preset="city" />

            {/* Glowing floating text */}
            <Float speed={2} rotationIntensity={0.1} floatIntensity={0.5}>
                <Text
                    ref={textRef}
                    position={[0, 0, 0]}
                    fontSize={3}
                    font="https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hjp-Ek-_EeA.woff"
                    letterSpacing={-0.05}
                    anchorX="center"
                    anchorY="middle"
                    characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"
                >
                    {text}
                    {/* Glassy, refractive material for the main text */}
                    <meshPhysicalMaterial 
                        color="#ffffff"
                        metalness={0.1}
                        roughness={0.1}
                        transmission={0.9}
                        thickness={1.5}
                        ior={1.5}
                        emissive={primaryColor}
                        emissiveIntensity={0.2}
                    />
                </Text>

                {subtitle && (
                    <Text
                        position={[0, -2.5, 0]}
                        fontSize={0.8}
                        font="https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hjp-Ek-_EeA.woff"
                        letterSpacing={0.2}
                        anchorX="center"
                        anchorY="middle"
                    >
                        {subtitle.toUpperCase()}
                        <meshStandardMaterial 
                            color={primaryColor} 
                            emissive={primaryColor}
                            emissiveIntensity={0.8}
                        />
                    </Text>
                )}
            </Float>

            {/* Dramatic Spotlight */}
            <spotLight 
                position={[10, 15, 10]} 
                angle={0.3} 
                penumbra={1} 
                intensity={2} 
                castShadow 
                color={primaryColor}
            />
            
            <spotLight 
                position={[-10, -10, 10]} 
                angle={0.5} 
                penumbra={1} 
                intensity={1} 
                color="#8E2DE2"
            />

            {/* Soft shadows directly below the text */}
            <ContactShadows 
                position={[0, -4, 0]} 
                opacity={0.4} 
                scale={20} 
                blur={2} 
                far={10} 
            />
        </group>
    );
};

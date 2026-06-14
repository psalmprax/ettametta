import React, { useRef, useMemo } from 'react';
import { useCurrentFrame } from 'remotion';
import { useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { random } from 'remotion';

export const LidarPointCloud: React.FC<{ primaryColor: string }> = ({ primaryColor }) => {
    const frame = useCurrentFrame();
    const pointsRef = useRef<THREE.Points>(null);

    // Generate a sphere/cloud of points
    const count = 10000;
    const [positions, colors] = useMemo(() => {
        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const color = new THREE.Color(primaryColor);
        
        for (let i = 0; i < count; i++) {
            // Random point on a sphere
            const theta = random(`t${i}`) * 2 * Math.PI;
            const phi = Math.acos((random(`p${i}`) * 2) - 1);
            const r = 3 + (random(`r${i}`) * 2);

            positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = r * Math.cos(phi);

            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }
        return [positions, colors];
    }, [primaryColor]);

    useFrame(() => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y = frame * 0.01;
            pointsRef.current.rotation.x = Math.sin(frame * 0.01) * 0.2;
            
            // Scanner effect
            const material = pointsRef.current.material as THREE.PointsMaterial;
            const sizePhase = (Math.sin(frame * 0.05) + 1) / 2;
            material.size = 0.02 + (sizePhase * 0.08);
        }
    });

    return (
        <group>
            <ambientLight intensity={0.5} />
            <Points ref={pointsRef} positions={positions} colors={colors}>
                <PointMaterial
                    transparent
                    vertexColors
                    size={0.05}
                    sizeAttenuation={true}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </Points>
        </group>
    );
};

import React from 'react';
import { AbsoluteFill } from 'remotion';

export type GradeType = 'warm_narrative' | 'electric_listicle' | 'dark_mystery' | 'cyberpunk' | 'classic_bw' | 'default';

interface ColorGradeProps {
    type: GradeType;
    intensity?: number;
}

export const ColorGrade: React.FC<ColorGradeProps> = ({ type, intensity = 1 }) => {
    if (type === 'default') return null;

    return (
        <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 5 }}>
            <svg style={{ position: 'absolute', width: 0, height: 0 }}>
                <filter id="warm_narrative_filter">
                    {/* Warm highlights, slight green/yellow tint in shadows */}
                    <feColorMatrix type="matrix" values="
                        1.1 0   0   0   0.05
                        0   1.0 0   0   0.02
                        0   0   0.9 0   -0.05
                        0   0   0   1   0" 
                    />
                    <feComponentTransfer>
                        <feRed type="gamma" exponent="0.9" />
                        <feGreen type="gamma" exponent="1.0" />
                        <feBlue type="gamma" exponent="1.1" />
                    </feComponentTransfer>
                </filter>

                <filter id="electric_listicle_filter">
                    {/* Teal and Orange vibes */}
                    <feColorMatrix type="matrix" values="
                        1.2 0   0   0   0.1
                        0   1.1 0   0   0
                        0   0   1.3 0   0.1
                        0   0   0   1   0" 
                    />
                    <feComponentTransfer>
                        <feRed type="table" tableValues="0 0.1 0.4 0.8 1" />
                        <feBlue type="table" tableValues="0 0.2 0.5 0.9 1" />
                    </feComponentTransfer>
                </filter>

                <filter id="dark_mystery_filter">
                    <feColorMatrix type="matrix" values="
                        0.8 0   0   0   -0.1
                        0   0.8 0   0   -0.1
                        0   0   1.1 0   0
                        0   0   0   1   0" 
                    />
                </filter>

                <filter id="cyberpunk_filter">
                    {/* Neon boost: crush blacks, push highlights, saturate */}
                    <feColorMatrix type="matrix" values="
                        1.3 0   0   0   -0.1
                        0   1.0 0   0   0
                        0   0   1.4 0   -0.05
                        0   0   0   1   0" 
                    />
                    <feComponentTransfer>
                        <feRed type="gamma" exponent="0.8" />
                        <feBlue type="gamma" exponent="0.8" />
                    </feComponentTransfer>
                </filter>

                <filter id="classic_bw_filter">
                    {/* Black & White conversion */}
                    <feColorMatrix type="saturate" values="0" />
                    <feComponentTransfer>
                        <feRed type="gamma" exponent="1.2" />
                        <feGreen type="gamma" exponent="1.2" />
                        <feBlue type="gamma" exponent="1.2" />
                    </feComponentTransfer>
                </filter>
            </svg>

            <AbsoluteFill style={{
                filter: `url(#${type}_filter)`,
                opacity: intensity,
                mixBlendMode: 'overlay'
            }} />
            
            {type === 'cyberpunk' && (
                <AbsoluteFill style={{
                    background: 'linear-gradient(45deg, rgba(255,0,255,0.1), rgba(0,255,255,0.1))',
                    mixBlendMode: 'screen'
                }} />
            )}
        </AbsoluteFill>
    );
};

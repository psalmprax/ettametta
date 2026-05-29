import React from 'react';
import { AbsoluteFill } from 'remotion';

export type GradeType = 'warm_narrative' | 'electric_listicle' | 'dark_mystery' | 'cyberpunk' | 'classic_bw' | 'retro_vhs' | 'horror_desaturated' | 'vibrant_bloom' | 'melancholic' | 'monochrome_high_contrast' | 'gold_luxury' | 'neon_hype' | 'default';

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
                        <feFuncR type="gamma" exponent="0.9" />
                        <feFuncG type="gamma" exponent="1.0" />
                        <feFuncB type="gamma" exponent="1.1" />
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
                        <feFuncR type="table" tableValues="0 0.1 0.4 0.8 1" />
                        <feFuncB type="table" tableValues="0 0.2 0.5 0.9 1" />
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
                        <feFuncR type="gamma" exponent="0.8" />
                        <feFuncB type="gamma" exponent="0.8" />
                    </feComponentTransfer>
                </filter>

                <filter id="classic_bw_filter">
                    {/* Black & White conversion */}
                    <feColorMatrix type="saturate" values="0" />
                    <feComponentTransfer>
                        <feFuncR type="gamma" exponent="1.2" />
                        <feFuncG type="gamma" exponent="1.2" />
                        <feFuncB type="gamma" exponent="1.2" />
                    </feComponentTransfer>
                </filter>

                <filter id="retro_vhs_filter">
                    {/* Retro VHS: warm fade, slight desaturation, lifted blacks */}
                    <feColorMatrix type="matrix" values="
                        1.1 0.05 0   0   0.05
                        0   1.0  0.05 0   0.03
                        0   0    0.85 0   0.08
                        0   0    0    1   0"
                    />
                    <feComponentTransfer>
                        <feFuncR type="linear" slope="0.9" intercept="0.05" />
                        <feFuncG type="linear" slope="0.9" intercept="0.05" />
                        <feFuncB type="linear" slope="0.85" intercept="0.08" />
                    </feComponentTransfer>
                </filter>

                <filter id="horror_desaturated_filter">
                    {/* Horror: heavy desaturation, crushed shadows, green tint */}
                    <feColorMatrix type="matrix" values="
                        0.7 0   0   0   -0.1
                        0   0.8 0   0   -0.05
                        0   0   0.7 0   -0.1
                        0   0   0   1   0"
                    />
                    <feComponentTransfer>
                        <feFuncR type="gamma" exponent="1.3" />
                        <feFuncG type="gamma" exponent="1.1" />
                        <feFuncB type="gamma" exponent="1.3" />
                    </feComponentTransfer>
                </filter>

                <filter id="vibrant_bloom_filter">
                    {/* Vibrant bloom: saturated, bright, punchy */}
                    <feColorMatrix type="matrix" values="
                        1.3 0   0   0   0.05
                        0   1.2 0   0   0.05
                        0   0   1.1 0   0
                        0   0   0   1   0"
                    />
                    <feComponentTransfer>
                        <feFuncR type="gamma" exponent="0.85" />
                        <feFuncG type="gamma" exponent="0.85" />
                        <feFuncB type="gamma" exponent="0.9" />
                    </feComponentTransfer>
                </filter>

                <filter id="melancholic_filter">
                    {/* Melancholic: cool blues, muted tones, lifted shadows */}
                    <feColorMatrix type="matrix" values="
                        0.9 0   0   0   0
                        0   0.9 0   0   0
                        0   0   1.2 0   0.1
                        0   0   0   1   0"
                    />
                    <feComponentTransfer>
                        <feFuncR type="linear" slope="0.85" intercept="0.1" />
                        <feFuncG type="linear" slope="0.85" intercept="0.1" />
                        <feFuncB type="linear" slope="0.95" intercept="0.05" />
                    </feComponentTransfer>
                </filter>

                <filter id="monochrome_high_contrast_filter">
                    {/* Monochrome high contrast: B&W with crushed blacks */}
                    <feColorMatrix type="saturate" values="0" />
                    <feComponentTransfer>
                        <feFuncR type="gamma" exponent="0.7" />
                        <feFuncG type="gamma" exponent="0.7" />
                        <feFuncB type="gamma" exponent="0.7" />
                    </feComponentTransfer>
                </filter>

                <filter id="gold_luxury_filter">
                    {/* Gold luxury: warm gold tones, rich shadows */}
                    <feColorMatrix type="matrix" values="
                        1.3 0.1 0   0   0.1
                        0   1.1 0.05 0   0.05
                        0   0   0.8 0   -0.05
                        0   0   0   1   0"
                    />
                    <feComponentTransfer>
                        <feFuncR type="gamma" exponent="0.9" />
                        <feFuncG type="gamma" exponent="0.95" />
                        <feFuncB type="gamma" exponent="1.1" />
                    </feComponentTransfer>
                </filter>

                <filter id="neon_hype_filter">
                    {/* Neon hype: high saturation, pushed highlights, cyan/magenta */}
                    <feColorMatrix type="matrix" values="
                        1.4 0   0   0   0
                        0   1.0 0   0   0.1
                        0   0   1.5 0   0.1
                        0   0   0   1   0"
                    />
                    <feComponentTransfer>
                        <feFuncR type="gamma" exponent="0.8" />
                        <feFuncB type="gamma" exponent="0.8" />
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
            {type === 'neon_hype' && (
                <AbsoluteFill style={{
                    background: 'linear-gradient(135deg, rgba(0,255,255,0.08), rgba(255,0,128,0.08))',
                    mixBlendMode: 'screen'
                }} />
            )}
            {type === 'gold_luxury' && (
                <AbsoluteFill style={{
                    background: 'linear-gradient(180deg, rgba(255,215,0,0.05), transparent)',
                    mixBlendMode: 'overlay'
                }} />
            )}
        </AbsoluteFill>
    );
};

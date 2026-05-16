import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

interface Word {
    word: string;
    start: number;
    end: number;
}

interface KineticCaptionsProps {
    words: Word[];
    primaryColor?: string;
    style?: string;
}

const EMOJI_MAP: Record<string, string> = {
    'money': '💰', 'cash': '💸', 'rich': '🤑', 'dead': '💀', 'heart': '❤️',
    'love': '🔥', 'fire': '🔥', 'crazy': '🤪', 'wow': '😲', 'stop': '🛑',
    'go': '🚀', 'win': '🏆', 'success': '📈', 'fail': '📉', 'warning': '⚠️',
    'divorce': '💔', 'regret': '😢', 'life': '🌱', 'time': '⏳', 'truth': '⚖️',
    'future': '🚀', 'danger': '☢️', 'power': '⚡', 'moneybag': '💰', 'shock': '😱'
};

export const WordCaptions: React.FC<KineticCaptionsProps> = ({ 
    words, 
    primaryColor = '#FFD700', 
    style: nexusStyle 
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Find active word
    const activeIndex = words.findIndex(w => frame >= w.start * fps && frame <= w.end * fps);
    
    // Nearest neighbor fallback
    const effectiveIndex = activeIndex !== -1 ? activeIndex : words.findIndex(w => frame < w.start * fps);
    const renderIndex = activeIndex !== -1 ? activeIndex : (effectiveIndex > 0 ? effectiveIndex - 1 : 0);
    
    if (words.length === 0) return null;

    // Show 3 words at a time for context
    const visibleWords = words.slice(renderIndex, renderIndex + 3);

    return (
        <AbsoluteFill style={{
            justifyContent: 'center',
            alignItems: 'center',
            paddingBottom: '20%',
            pointerEvents: 'none'
        }}>
            <div style={{
                display: 'flex',
                gap: '20px',
                alignItems: 'center',
                perspective: '1000px'
            }}>
                {visibleWords.map((wordObj, i) => {
                    const isPrimary = i === 0 && activeIndex !== -1;
                    const cleanWord = wordObj.word.toLowerCase().replace(/[^\w]/g, '');
                    const emoji = EMOJI_MAP[cleanWord];

                    const wordSpring = spring({
                        frame: frame - (wordObj.start * fps),
                        fps,
                        config: { damping: 10, stiffness: 120 }
                    });

                    // Dynamic styles based on active state
                    const scale = isPrimary ? interpolate(wordSpring, [0, 1], [0.8, 1.3]) : 0.9;
                    const opacity = isPrimary ? 1 : interpolate(wordSpring, [0, 1], [0.4, 0.6]);
                    const blur = isPrimary ? 0 : 2;
                    const rotate = isPrimary ? interpolate(wordSpring, [0, 1], [10, -3]) : 0;
                    const color = isPrimary ? primaryColor : 'white';

                    return (
                        <div key={`${wordObj.word}-${i}`} style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            transform: `scale(${scale}) rotate(${rotate}deg)`,
                            opacity,
                            filter: `blur(${blur}px)`,
                            transition: 'all 0.1s ease-out'
                        }}>
                            {isPrimary && emoji && (
                                <div style={{ 
                                    fontSize: '100px', 
                                    marginBottom: '-20px',
                                    filter: 'drop-shadow(0 0 20px rgba(0,0,0,0.5))'
                                }}>
                                    {emoji}
                                </div>
                            )}
                            <h1 style={{
                                fontSize: '120px',
                                fontWeight: 900,
                                color,
                                textTransform: 'uppercase',
                                textAlign: 'center',
                                margin: 0,
                                WebkitTextStroke: isPrimary ? '4px black' : '2px black',
                                textShadow: isPrimary ? '8px 8px 0px rgba(0,0,0,1)' : '4px 4px 0px rgba(0,0,0,0.8)',
                                fontFamily: nexusStyle === 'HEARTFELT_NARRATIVE' ? 'Georgia, serif' : 'Inter, sans-serif',
                                fontStyle: nexusStyle === 'HEARTFELT_NARRATIVE' ? 'italic' : 'normal',
                                letterSpacing: '-4px'
                            }}>
                                {wordObj.word}
                            </h1>
                        </div>
                    );
                })}
            </div>
        </AbsoluteFill>
    );
};

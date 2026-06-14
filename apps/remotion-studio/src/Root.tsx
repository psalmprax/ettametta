import React, { useEffect, useState } from 'react';
import { Composition } from 'remotion';
import { ViralClip, viralClipSchema } from './Composition';
import { CinematicMinimal, cinematicMinimalSchema } from './templates/CinematicMinimal';
import { HormoziStyle, hormoziStyleSchema } from './templates/HormoziStyle';
import { Cinematic3D, cinematic3DSchema } from './templates/Cinematic3D';
import { CinematicAncient, cinematicAncientSchema } from './templates/CinematicAncient';
import { CinematicIridescent, cinematicIridescentSchema } from './templates/CinematicIridescent';
import { CinematicPortal, cinematicPortalSchema } from './templates/CinematicPortal';
import { CinematicCyberpunk, cinematicCyberpunkSchema } from './templates/CinematicCyberpunk';
import { CinematicLiquid, cinematicLiquidSchema } from './templates/CinematicLiquid';
import { CinematicPrism, cinematicPrismSchema } from './templates/CinematicPrism';
import { CinematicLidar, cinematicLidarSchema } from './templates/CinematicLidar';
import { CinematicKinetic, cinematicKineticSchema } from './templates/CinematicKinetic';

export const RemotionRoot: React.FC = () => {
    const [jobData, setJobData] = useState<any>(null);

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const jobId = urlParams.get('job_id');
        if (jobId) {
            // Real-First: Fetch from the production API
            fetch(`http://149.104.110.122.sslip.io:7200/api/v1/transformation/jobs/${jobId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.data) {
                        const job = data.data;
                        const meta = job.job_metadata || {};
                        setJobData({
                            title: meta.title || 'Studio Intelligence',
                            subtitle: meta.description || 'Neural Refinement in Progress',
                            video_url: job.result_url || meta.video_url,
                            timeline: meta.timeline || [],
                            brand_name: meta.brand_name || 'ettametta',
                            primary_color: meta.primary_color || '#8b5cf6'
                        });
                    }
                })
                .catch(err => console.error("Remotion Studio: Failed to fetch job data", err));
        }
    }, []);

    return (
        <>
            <Composition
                id="ViralClip"
                component={ViralClip}
                durationInFrames={18000}
                fps={30}
                width={1080}
                height={1920}
                schema={viralClipSchema}
                defaultProps={jobData || {
                    title: 'Your Viral Hook Here',
                    subtitle: 'Captivating content follows...',
                    audio_url: undefined,
                    show_cta_overlay: true,
                    cta_type: 'engagement',
                    cta_text: 'Like & Subscribe for more!',
                    words: [],
                    clips: [],
                    trademark_url: undefined,
                    brand_name: 'ettametta',
                    primary_color: '#8b5cf6',
                    vignette_intensity: 0.5,
                    grain_opacity: 0.08,
                    style: 'CINEMATIC_DOC',
                    job_metadata: {}
                }}
            />
            <Composition
                id="CinematicMinimal"
                component={CinematicMinimal}
                durationInFrames={18000}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicMinimalSchema}
                defaultProps={{
                    title: 'Your Title Here',
                    subtitle: 'Captivating Subtitle',
                    primary_color: '#00F2FE',
                    show_cta_overlay: true,
                    cta_type: 'engagement',
                    cta_text: 'Like & Subscribe'
                }}
            />
            <Composition
                id="HormoziStyle"
                component={HormoziStyle}
                durationInFrames={18000}
                fps={30}
                width={1080}
                height={1920}
                schema={hormoziStyleSchema}
                defaultProps={{
                    text: 'Results Discipline Money Freedom Legacy',
                    highlight_color: '#00ff00',
                    show_cta_overlay: true,
                    cta_type: 'cta',
                    cta_text: 'Link in bio'
                }}
            />
            <Composition
                id="Cinematic3D"
                component={Cinematic3D}
                durationInFrames={18000}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematic3DSchema}
                defaultProps={{
                    title: 'ETTAMETTA PRESENTS',
                    subtitle: 'AI Documentary Engine',
                    primary_color: '#00F2FE',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicAncient"
                component={CinematicAncient}
                durationInFrames={18000}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicAncientSchema}
                defaultProps={{
                    title: 'ETTAMETTA PRESENTS',
                    subtitle: 'AI Documentary Engine',
                    primary_color: '#FFD700',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicIridescent"
                component={CinematicIridescent}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicIridescentSchema}
                defaultProps={{
                    title: 'AURORA',
                    subtitle: 'COLLECTION',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicPortal"
                component={CinematicPortal}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicPortalSchema}
                defaultProps={{
                    title: 'ANCIENT',
                    subtitle: 'MYSTERY',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicCyberpunk"
                component={CinematicCyberpunk}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicCyberpunkSchema}
                defaultProps={{
                    title: 'SYSTEM',
                    subtitle: 'ONLINE',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicLiquid"
                component={CinematicLiquid}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicLiquidSchema}
                defaultProps={{
                    title: 'LIQUID',
                    subtitle: 'METAL',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicPrism"
                component={CinematicPrism}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicPrismSchema}
                defaultProps={{
                    title: 'OPTICAL',
                    subtitle: 'PRISM',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicLidar"
                component={CinematicLidar}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicLidarSchema}
                defaultProps={{
                    title: 'LIDAR',
                    subtitle: 'SCANNER',
                    show_cta_overlay: false
                }}
            />
            <Composition
                id="CinematicKinetic"
                component={CinematicKinetic}
                durationInFrames={120}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicKineticSchema}
                defaultProps={{
                    title: 'KINETIC',
                    subtitle: 'ENERGY',
                    show_cta_overlay: false
                }}
            />
        </>
    );
};

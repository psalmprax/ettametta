import React, { useEffect, useState } from 'react';
import { Composition } from 'remotion';
import { ViralClip, viralClipSchema } from './Composition';
import { CinematicMinimal, cinematicMinimalSchema } from './templates/CinematicMinimal';
import { HormoziStyle, hormoziStyleSchema } from './templates/HormoziStyle';

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
                durationInFrames={300}
                fps={30}
                width={1080}
                height={1920}
                schema={viralClipSchema}
                defaultProps={jobData || {
                    title: 'Your Viral Hook Here',
                    subtitle: 'Captivating content follows...',
                    video_url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                }}
            />
            {/* ... other compositions ... */}
        </>
    );
};

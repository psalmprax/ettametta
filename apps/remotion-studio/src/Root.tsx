import { Composition } from 'remotion';
import { ViralClip, viralClipSchema } from './Composition';

export const RemotionRoot: React.FC = () => {
    return (
        <>
            <Composition
                id="ViralClip"
                component={ViralClip}
                durationInFrames={300} // 10 seconds @ 30fps
                fps={30}
                width={1080}
                height={1920}
                schema={viralClipSchema}
                defaultProps={{
                    title: 'Your Viral Hook Here',
                    subtitle: 'Captivating content follows...',
                    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                }}
            />
        </>
    );
};

import { Composition } from 'remotion';
import { ViralClip, viralClipSchema } from './Composition';
import { CinematicMinimal, cinematicMinimalSchema } from './templates/CinematicMinimal';
import { HormoziStyle, hormoziStyleSchema } from './templates/HormoziStyle';

export const RemotionRoot: React.FC = () => {
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
                defaultProps={{
                    title: 'Your Viral Hook Here',
                    subtitle: 'Captivating content follows...',
                    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                }}
            />
            <Composition
                id="CinematicMinimal"
                component={CinematicMinimal}
                durationInFrames={300}
                fps={30}
                width={1080}
                height={1920}
                schema={cinematicMinimalSchema}
                defaultProps={{
                    title: 'Silent Velocity',
                    subtitle: 'Architecture of the Future',
                }}
            />
            <Composition
                id="HormoziStyle"
                component={HormoziStyle}
                durationInFrames={300}
                fps={30}
                width={1080}
                height={1920}
                schema={hormoziStyleSchema}
                defaultProps={{
                    text: 'WORK HARDER THAN EVERYONE ELSE UNTIL YOU WIN',
                    highlightColor: '#00ff00'
                }}
            />
        </>
    );
};

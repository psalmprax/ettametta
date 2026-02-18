from moviepy import AudioFileClip, CompositeAudioClip
import logging

class AudioMixer:
    @staticmethod
    def mix_tracks(voiceover_path: str, music_path: str, duration: float, voice_vol: float = 1.0, music_vol: float = 0.1) -> CompositeAudioClip:
        """
        Mixes voiceover and background music with basic volume leveling.
        """
        try:
            voice = AudioFileClip(voiceover_path).with_volume_scaled(voice_vol)
            
            # Load music and loop if shorter than voiceover
            music = AudioFileClip(music_path).with_volume_scaled(music_vol)
            if music.duration < duration:
                # Basic looping logic
                music = music.with_effects([lambda clip: clip.with_duration(duration)]) # Simplistic stretch for now
            
            # Trim music to duration
            music = music.with_duration(duration)
            
            # Apply ducking (placeholder for complex ducking)
            # In a real app, we'd use .with_volume_scaled with a function to dip volume during voice
            
            return CompositeAudioClip([voice, music])
        except Exception as e:
            logging.error(f"[AudioMixer] Mix Error: {e}")
            return None

base_audio_mixer = AudioMixer()

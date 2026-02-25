import os
import logging
import subprocess

class AudioMixer:
    @staticmethod
    def mix_tracks(voiceover_path: str, music_path: str, duration: float, voice_vol: float = 1.0, music_vol: float = 0.1) -> str:
        """
        Mixes voiceover and background music using FFmpeg.
        Replaces MoviePy for better performance.
        """
        try:
            output_path = voiceover_path.replace(".mp3", "_mixed.mp3")
            
            # Simple FFmpeg command for mixing two audio tracks
            # [0:a] is voiceover, [1:a] is music
            # volume=music_vol dips the music
            cmd = [
                "ffmpeg", "-y",
                "-i", voiceover_path,
                "-i", music_path,
                "-filter_complex", f"[0:a]volume={voice_vol}[v];[1:a]volume={music_vol}[m];[v][m]amix=inputs=2:duration=first",
                "-acodec", "libmp3lame",
                output_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return output_path
            
        except Exception as e:
            logging.error(f"[AudioMixer] FFmpeg Mix Error: {e}")
            return None

base_audio_mixer = AudioMixer()

"""
Rhythm Analysis Engine for Elite Cinematic Fusion
==================================================

Uses librosa to extract BPM and beat markers from background music
or narration to allow rhythmic synchronization of visual cuts.
"""

import os
import logging
from typing import Any
import numpy as np

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    librosa = None

logger = logging.getLogger(__name__)

class RhythmEngine:
    """
    Analyzes audio files to extract rhythm markers and sync points.
    """

    def __init__(self):
        if not LIBROSA_AVAILABLE:
            logger.warning("[Rhythm] librosa not installed. Rhythmic sync will be disabled.")

    def get_beat_markers(self, audio_path: str, sr: int = 22050) -> dict[str, Any]:
        """
        Extracts beat timestamps and onset strength from an audio file.

        Args:
            audio_path: Path to the audio file (MP3, WAV, etc.)
            sr: Sample rate for analysis

        Returns:
            dict containing 'bpm', 'beats' (list of seconds), and 'onsets' (energy peak indices)
        """
        if not LIBROSA_AVAILABLE or not os.path.exists(audio_path):
            return {"bpm": 0, "beats": [], "onsets": []}

        try:
            # Load the audio file
            y, sr = librosa.load(audio_path, sr=sr)

            # 1. Estimate tempo and beat markers
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

            # 2. Extract onset strength (to find extra emphasis points)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            # Find peaks in the onset envelope
            onset_frames = librosa.util.peak_pick(onset_env, pre_max=7, post_max=7, pre_avg=7, post_avg=7, delta=0.5, wait=7)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()

            # Ensure BPM is a scalar
            bpm = float(tempo[0]) if isinstance(tempo, (list, np.ndarray)) else float(tempo)

            logger.info(f"[Rhythm] Analyzed {audio_path}: BPM={bpm:.2f}, Beats={len(beat_times)}")

            return {
                "bpm": bpm,
                "beats": beat_times,
                "onsets": onset_times,
                "total_duration": librosa.get_duration(y=y, sr=sr)
            }

        except Exception as e:
            logger.exception(f"[Rhythm] Analysis failed: {e}")
            return {"bpm": 0, "beats": [], "onsets": [], "error": str(e)}

    def find_nearest_beat(self, timestamp: float, beat_markers: list[float], tolerance: float = 0.5) -> float:
        """
        Finds the beat marker closest to a target timestamp.
        Used to "snap" video cuts to the nearest beat.
        """
        if not beat_markers:
            return timestamp

        markers = np.asarray(beat_markers, dtype=float)
        diffs = np.abs(markers - timestamp)
        min_idx = int(np.argmin(diffs))

        if diffs[min_idx] <= tolerance:
            return float(beat_markers[min_idx])

        return timestamp

# Singleton instance
base_rhythm_service = RhythmEngine()

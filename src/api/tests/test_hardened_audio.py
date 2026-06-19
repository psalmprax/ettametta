import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.audio.sound_design import SoundDesignService
from src.services.audio.voiceover import VoiceoverService

@pytest.fixture
def mock_audio_paths(tmp_path):
    """Create mock audio files for testing."""
    voice_path = tmp_path / "voice.mp3"
    voice_path.write_bytes(b"fake voice data")
    bg_path = tmp_path / "music.mp3"
    bg_path.write_bytes(b"fake music data")
    return str(voice_path), str(bg_path)

@pytest.mark.anyio
class TestHardenedSoundDesign:
    async def test_mix_audio_tracks_enabled_logic(self, mock_audio_paths):
        """Test that SoundDesignService mixes tracks when enabled."""
        voice_path, bg_path = mock_audio_paths
        service = SoundDesignService()
        service.enabled = True
        
        # Patch the imports inside the method scope by patching the modules in sys.modules
        with patch("moviepy.audio.AudioClip.CompositeAudioClip") as mock_composite:
            with patch("moviepy.AudioFileClip") as mock_afc:
                mock_clip = MagicMock()
                mock_clip.duration = 10.0
                mock_afc.return_value = mock_clip
                
                mock_mixed = MagicMock()
                mock_composite.return_value = mock_mixed
                
                # Mock the export
                mock_mixed.write_audiofile = MagicMock()
                
                result = await service.mix_audio_tracks(voice_path, bg_path)
                
                assert result is not None
                assert "mixed_" in result
                # Just verify it didn't return the original voice path (which happens on error/disabled)
                assert result != voice_path

    async def test_mix_audio_tracks_disabled_fallback(self, mock_audio_paths):
        """Test that SoundDesignService returns original path when disabled."""
        voice_path, bg_path = mock_audio_paths
        service = SoundDesignService()
        service.enabled = False
        
        result = await service.mix_audio_tracks(voice_path, bg_path)
        assert result == voice_path

@pytest.mark.anyio
class TestHardenedVoiceover:
    async def test_voiceover_engine_selection_fish(self):
        """Test Fish Speech engine selection."""
        service = VoiceoverService()
        with patch("services.voiceover.service.get_secret") as mock_secret:
            mock_secret.side_effect = lambda key, default=None: "fish_speech" if key == "voice_engine" else default
            
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = MagicMock(status_code=200, json=lambda: {"audio_uri": "/test.mp3"})
                with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = MagicMock(status_code=200, content=b"fake audio")
                    
                    # Mock file creation
                    with patch("builtins.open", MagicMock()):
                        result = await service.generate_voiceover("Hello World")
                        assert result is not None
                        assert "audio/voiceover_" in result

    async def test_voiceover_fallback_to_gtts(self):
        """Test fallback to gTTS when cloud APIs fail."""
        service = VoiceoverService()
        with patch("services.voiceover.service.get_secret", return_value="elevenlabs"):
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = Exception("Connection Failed")
                
                with patch("gtts.gTTS") as mock_gtts:
                    mock_gtts_instance = MagicMock()
                    mock_gtts.return_value = mock_gtts_instance
                    
                    result = await service.generate_voiceover("Hello Fallback")
                    assert result is not None
                    assert mock_gtts.called

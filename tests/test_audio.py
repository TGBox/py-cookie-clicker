import tempfile
from pathlib import Path

from src.audio import AudioManager, generate_sound_effects


def test_sound_file_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        sounds_dir = Path(tmpdir)
        sound_paths = generate_sound_effects(sounds_dir)

        assert "click" in sound_paths
        assert "crit" in sound_paths
        assert "buy" in sound_paths
        assert "comet" in sound_paths

        for path in sound_paths.values():
            assert path.exists()
            assert path.stat().st_size > 44  # WAV header is 44 bytes


def test_audio_manager_mute_toggle():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AudioManager(sounds_dir=Path(tmpdir), enabled=True)
        assert manager.enabled is True

        manager.set_enabled(False)
        assert manager.enabled is False

        # Playing while disabled should not raise errors
        manager.play_click()
        manager.play_buy()
        manager.play_comet()

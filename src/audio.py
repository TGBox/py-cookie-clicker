"""Procedural retro sound effects synthesis and audio management."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

# On Windows, winsound provides instantaneous, zero-dependency async audio playback.
try:
    import winsound
except ImportError:
    winsound = None


def _write_sine_wave(
    filepath: Path,
    frequencies: list[float],
    duration: float = 0.1,
    sample_rate: int = 22050,
    volume: float = 0.4,
    sweep_to: float | None = None,
) -> None:
    """Generate and write a 16-bit mono WAV file."""
    num_samples = int(sample_rate * duration)
    frames = bytearray()

    for i in range(num_samples):
        t = i / sample_rate
        # Linear envelope to avoid clicking artifacts
        decay = 1.0 - (i / num_samples)
        attack = min(1.0, i / (sample_rate * 0.005))
        envelope = decay * attack

        sample_val = 0.0
        for base_freq in frequencies:
            freq = base_freq
            if sweep_to is not None:
                freq = base_freq + (sweep_to - base_freq) * (i / num_samples)
            sample_val += math.sin(2.0 * math.pi * freq * t)

        sample_val = (sample_val / len(frequencies)) * volume * envelope
        # Clamp to 16-bit signed integer range
        int_val = int(max(-32767, min(32767, sample_val * 32767)))
        frames.extend(struct.pack("<h", int_val))

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(filepath), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def generate_sound_effects(directory: Path) -> dict[str, Path]:
    """Generate standard sound effect WAV files in `directory`."""
    directory.mkdir(parents=True, exist_ok=True)
    sounds: dict[str, Path] = {}

    # 1. Click / Laser zap: frequency sweep 800Hz -> 200Hz, 60ms
    click_path = directory / "click.wav"
    _write_sine_wave(click_path, [800.0], duration=0.06, volume=0.35, sweep_to=200.0)
    sounds["click"] = click_path

    # 2. Critical hit: bright harmonic chord (880Hz, 1320Hz, 1760Hz), 120ms
    crit_path = directory / "crit.wav"
    _write_sine_wave(crit_path, [880.0, 1320.0, 1760.0], duration=0.12, volume=0.45)
    sounds["crit"] = crit_path

    # 3. Buy / Purchase: ascending chime (523Hz -> 659Hz -> 784Hz), 140ms
    buy_path = directory / "buy.wav"
    _write_sine_wave(buy_path, [523.25], duration=0.14, volume=0.4, sweep_to=784.0)
    sounds["buy"] = buy_path

    # 4. Comet spawn/click: celestial shimmer glissando, 250ms
    comet_path = directory / "comet.wav"
    _write_sine_wave(comet_path, [660.0, 990.0], duration=0.25, volume=0.5, sweep_to=1400.0)
    sounds["comet"] = comet_path

    return sounds


class AudioManager:
    """Manages audio settings and plays synthesized sound effects asynchronously."""

    def __init__(self, sounds_dir: Path | None = None, enabled: bool = True):
        self.sounds_dir = sounds_dir or (Path(__file__).parent / "assets" / "sounds")
        self.enabled = enabled
        self._sound_paths: dict[str, Path] = generate_sound_effects(self.sounds_dir)

    def set_enabled(self, enabled: bool) -> None:
        """Toggle audio on/off."""
        self.enabled = enabled

    def _play(self, sound_name: str) -> None:
        if not self.enabled or not winsound:
            return
        path = self._sound_paths.get(sound_name)
        if path and path.exists():
            try:
                winsound.PlaySound(
                    str(path),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
            except OSError:
                pass

    def play_click(self, crit: bool = False) -> None:
        self._play("crit" if crit else "click")

    def play_buy(self) -> None:
        self._play("buy")

    def play_comet(self) -> None:
        self._play("comet")

import array
import math
import random

import pygame

SAMPLE_RATE = 44100


def _envelope(i, n, fade_n):
    if fade_n <= 0:
        return 1.0
    if i < fade_n:
        return i / fade_n
    if i > n - fade_n:
        return max(0.0, (n - i) / fade_n)
    return 1.0


def tone(freq_start, duration, volume=0.5, freq_end=None, fade=0.015, wave="sine"):
    n = max(1, int(SAMPLE_RATE * duration))
    freq_end = freq_start if freq_end is None else freq_end
    fade_n = max(1, int(SAMPLE_RATE * fade))
    samples = array.array("h")
    phase = 0.0
    for i in range(n):
        f = freq_start + (freq_end - freq_start) * (i / n)
        phase += 2 * math.pi * f / SAMPLE_RATE
        s = math.sin(phase)
        if wave == "square":
            s = 1.0 if s >= 0 else -1.0
        elif wave == "triangle":
            s = (2 / math.pi) * math.asin(math.sin(phase))
        env = _envelope(i, n, fade_n)
        samples.append(int(max(-32000, min(32000, 32000 * volume * s * env))))
    return samples


def noise(duration, volume=0.4, fade=0.05, smoothing=0.0):
    n = max(1, int(SAMPLE_RATE * duration))
    fade_n = max(1, int(SAMPLE_RATE * fade))
    samples = array.array("h")
    prev = 0.0
    for i in range(n):
        raw = random.uniform(-1, 1)
        if smoothing > 0:
            prev += smoothing * (raw - prev)
            raw = prev
        env = _envelope(i, n, fade_n)
        samples.append(int(max(-32000, min(32000, 32000 * volume * raw * env))))
    return samples


def concat(*parts):
    out = array.array("h")
    for p in parts:
        out.extend(p)
    return out


def mix(*parts):
    n = max(len(p) for p in parts)
    out = array.array("h", [0] * n)
    for p in parts:
        for i, v in enumerate(p):
            out[i] = max(-32767, min(32767, out[i] + v))
    return out


def to_sound(samples):
    return pygame.mixer.Sound(buffer=array.array("h", samples).tobytes())


class SoundBank:
    """Procedurally synthesized sound effects (no external audio files)."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        except Exception:
            pass

    def init(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self._build()
            self.enabled = True
        except Exception:
            self.enabled = False

    def _build(self):
        self.sounds["jump"] = to_sound(tone(320, 0.14, volume=0.5, freq_end=680, wave="triangle"))
        self.sounds["step"] = to_sound(noise(0.035, volume=0.22, fade=0.01, smoothing=0.6))
        self.sounds["finish"] = to_sound(
            concat(
                tone(523, 0.11, volume=0.4, wave="triangle"),
                tone(659, 0.11, volume=0.4, wave="triangle"),
                tone(784, 0.11, volume=0.4, wave="triangle"),
                tone(1046, 0.22, volume=0.45, wave="triangle"),
            )
        )
        self.sounds["select"] = to_sound(tone(500, 0.05, volume=0.35, freq_end=760, wave="square"))
        self.sounds["bump"] = to_sound(
            mix(
                tone(130, 0.1, volume=0.4, freq_end=70, wave="sine", fade=0.005),
                noise(0.06, volume=0.3, fade=0.01, smoothing=0.2),
            )
        )
        self.sounds["boost"] = to_sound(tone(300, 0.18, volume=0.5, freq_end=900, wave="sine", fade=0.01))

    def play(self, name, volume=1.0):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.set_volume(volume)
            snd.play()

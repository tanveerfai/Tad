"""Audio capture module - records system/microphone audio non-intrusively."""

import os
import wave
import threading
import datetime
import numpy as np
import sounddevice as sd


class AudioCapture:
    """Captures audio from system output or microphone without disrupting the meeting."""

    def __init__(self, output_dir="output", sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.output_dir = output_dir
        self.is_recording = False
        self._audio_frames = []
        self._lock = threading.Lock()
        self._stream = None
        os.makedirs(output_dir, exist_ok=True)

    def _get_loopback_device(self):
        """Find a loopback/monitor device to capture system audio.

        On Linux: looks for PulseAudio monitor devices.
        On Windows: looks for WASAPI loopback devices.
        On macOS: requires BlackHole or similar virtual audio device.
        """
        devices = sd.query_devices()
        # Look for monitor/loopback devices (Linux PulseAudio)
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if "monitor" in name or "loopback" in name or "stereo mix" in name:
                if dev["max_input_channels"] > 0:
                    return i

        # Fallback: look for virtual audio cables (macOS BlackHole, Windows VB-Cable)
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if any(kw in name for kw in ["blackhole", "vb-cable", "virtual"]):
                if dev["max_input_channels"] > 0:
                    return i

        return None

    def list_devices(self):
        """List all available audio input devices."""
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append({"id": i, "name": dev["name"], "channels": dev["max_input_channels"]})
        return input_devices

    def _audio_callback(self, indata, frames, time_info, status):
        """Called for each audio block during recording."""
        with self._lock:
            self._audio_frames.append(indata.copy())

    def start_recording(self, device=None, use_loopback=True):
        """Start recording audio.

        Args:
            device: Specific device ID to use. If None, auto-detects.
            use_loopback: If True, tries to capture system audio (what you hear).
                          If False, uses the default microphone.
        """
        if self.is_recording:
            return

        if device is None and use_loopback:
            device = self._get_loopback_device()

        self._audio_frames = []
        self.is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=device,
            callback=self._audio_callback,
            dtype="float32",
        )
        self._stream.start()

    def stop_recording(self):
        """Stop recording and save the audio to a WAV file.

        Returns:
            Path to the saved WAV file, or None if no audio was captured.
        """
        if not self.is_recording:
            return None

        self.is_recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._audio_frames:
                return None
            audio_data = np.concatenate(self._audio_frames, axis=0)
            self._audio_frames = []

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.output_dir, f"meeting_{timestamp}.wav")

        # Convert float32 to int16 for WAV file
        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return filepath

    def get_recording_duration(self):
        """Get the current recording duration in seconds."""
        with self._lock:
            if not self._audio_frames:
                return 0.0
            total_frames = sum(f.shape[0] for f in self._audio_frames)
            return total_frames / self.sample_rate

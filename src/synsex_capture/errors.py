"""Custom exceptions for synsex-capture."""


class SynsexCaptureError(Exception):
    """Base exception for domain-level errors."""


class MidiPortError(SynsexCaptureError):
    """Raised when MIDI port operations fail."""


class SyxFileError(SynsexCaptureError):
    """Raised when .syx file operations fail."""

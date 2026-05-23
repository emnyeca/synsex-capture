"""Custom exceptions for digitone-syx-toolkit."""


class DigitoneToolkitError(Exception):
    """Base exception for domain-level errors."""


class MidiPortError(DigitoneToolkitError):
    """Raised when MIDI port operations fail."""


class SyxFileError(DigitoneToolkitError):
    """Raised when .syx file operations fail."""

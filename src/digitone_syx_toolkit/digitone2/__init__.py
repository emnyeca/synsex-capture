"""Digitone II specific builder helpers."""

__all__ = ["build_digitone2_syx"]


def __getattr__(name: str):
	if name == "build_digitone2_syx":
		from .builder import build_digitone2_syx

		return build_digitone2_syx
	raise AttributeError(name)

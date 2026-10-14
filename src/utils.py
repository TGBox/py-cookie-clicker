"""Formatting utilities for German number notation and compact currency display."""

from __future__ import annotations


def format_number(val: float, precision: int = 2) -> str:
    """Format large numbers with German abbreviation suffix (Mio., Mrd., Bio.)."""
    if val < 0:
        return f"-{format_number(-val, precision)}"

    if val < 1000.0:
        return f"{round(val):d}"

    if val < 1_000_000.0:
        # German thousands separator is dot
        return f"{round(val):,d}".replace(",", ".")

    suffixes = [
        (1_000_000_000_000_000.0, "Brd."),
        (1_000_000_000_000.0, "Bio."),
        (1_000_000_000.0, "Mrd."),
        (1_000_000.0, "Mio."),
    ]

    for limit, suffix in suffixes:
        if val >= limit:
            scaled = val / limit
            formatted = f"{scaled:.{precision}f}".replace(".", ",")
            return f"{formatted} {suffix}"

    return f"{round(val):,d}".replace(",", ".")

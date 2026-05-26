"""Module registry — single source of truth for all modules.

New modules only need to call register() once (usually from their __init__.py).
This removes the hardcoded duplication across app.py, home.py, and about.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from textual.screen import Screen


@dataclass(frozen=True, slots=True)
class ModuleMeta:
    """Static metadata for a module + optional lazy loader for its Screen."""

    id: str
    num: str
    icon: str
    title: str
    subtitle: str
    desc: str
    difficulty: str
    topics: str
    available: bool = True
    # Lazy loader so we don't import every screen at startup
    screen_loader: Callable[[], type[Screen]] | None = None


_REGISTRY: dict[str, ModuleMeta] = {}


def register(meta: ModuleMeta) -> None:
    """Register a module. Idempotent for the same id (allows reload in dev)."""
    if meta.id in _REGISTRY:
        # Allow re-registration in development (e.g. during `python -m`)
        pass
    _REGISTRY[meta.id] = meta


def get_module(module_id: str) -> ModuleMeta:
    """Return metadata for a single module."""
    return _REGISTRY[module_id]


def get_all_modules() -> list[ModuleMeta]:
    """All registered modules, sorted by their display number."""
    return sorted(_REGISTRY.values(), key=lambda m: m.num)


def get_available_modules() -> list[ModuleMeta]:
    """Only modules that are currently playable."""
    return [m for m in get_all_modules() if m.available]


def get_screens() -> dict[str, type[Screen]]:
    """Mapping suitable for App.SCREENS = {id: ScreenClass, ...}."""
    screens: dict[str, type[Screen]] = {}
    for m in _REGISTRY.values():
        if m.screen_loader is not None:
            screens[m.id] = m.screen_loader()
    return screens


def get_locked_modules() -> list[ModuleMeta]:
    """Modules shown on the home grid but not yet implemented."""
    return [m for m in get_all_modules() if not m.available]

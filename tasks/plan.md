# Implementation Plan: py-cookie-clicker (Cosmic Asteroid Miner)

## Overview

Transform `py-cookie-clicker` into a high-polish space asteroid mining clicker desktop game built with PySide6. The player mines "Sternenstaub" (Cosmic Dust / Ore) by clicking a massive cosmic asteroid and purchases automated mining structures (mining drones, orbital lasers, refineries, Dyson spheres) and upgrades. Features include random golden comets, floating click feedback, achievements, sound effects, dark sci-fi UI styling, persistent savegames with export/import, and fullscreen (F11) support.

## Architecture Decisions

- **Domain Layer (`src/models.py`, `src/game_engine.py`)**: Pure Python domain logic decoupled from Qt widgets. Testable via `pytest` without UI harness.
- **Persistence Layer (`src/save_manager.py`)**: Robust JSON-based savegame format with schema versioning, autosave (every 30s + on quit), manual save, and string export/import.
- **Audio Layer (`src/audio.py`)**: Lightweight synthesized retro SFX generated via stdlib `wave`/`struct` without heavy external dependencies, played via `QSoundEffect` with mute toggle.
- **UI & Presentation Layer (`src/widgets/`, `src/main.py`)**: Event-driven HUD updates (Qt signals), animated asteroid with floating click numbers, responsive layout, dark sci-fi stylesheet, F11 fullscreen support, and window position persistence in `QSettings`.
- **Assets (`src/assets/`)**: Generated PNG art assets for asteroid, comets, and space structures.

## Task List

### Phase 1: Foundation & Pure Domain Logic (TDD)

- [x] Task 1: Core Economy & Data Models (`Building`, `Upgrade`, `Achievement`, `GameState`) with formulas for cost scaling and OpS (Ore per second).
- [x] Task 2: Game Engine & Event Loop (passive production, manual clicks, comet spawning logic, critical clicks).
- [x] Task 3: Savegame Manager (JSON serialization, deserialization, export/import base64 string, default state, corruption recovery).

### Checkpoint 1: Domain & Tests

- [x] All unit tests pass with `uv run pytest`.
- [x] Code passes `uv run ruff check`.

### Phase 2: Assets & Audio Generation

- [x] Task 4: Generate visual PNG game assets (Asteroid, Golden Comet, Mining Drone, Orbital Refinery, Dyson Sphere, etc.).
- [x] Task 5: Lightweight sound effects generator & manager with mute toggle.

### Phase 3: PySide6 GUI Components & UX

- [x] Task 6: Interactive Asteroid Widget with click squeeze animation, floating text numbers, and comet overlay.
- [x] Task 7: Shop & Upgrades Panel with responsive building cards, buy multiplier (x1, x10, x100, max), and tooltips.
- [x] Task 8: HUD, Statistics & Settings Dialog (Achievements, Save Export/Import, Reset, Sound Toggle).
- [x] Task 9: Assemble MainWindow, F11 fullscreen toggle, QSettings geometry persistence, auto-save timer, and sci-fi QSS styling.

### Checkpoint 2: Integration & Verification

- [x] Run full pytest test suite.
- [x] Run ruff format & lint.
- [x] Launch application test and verify all mechanics end-to-end.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ------ | -------- | ------------ |
| PySide6 GUI event loop blocking | High | Keep engine ticks on `QTimer` (100ms or 50ms) and all math lightweight. |
| Savegame format corruption | High | Atomic file writes (`.tmp` -> replace) with fallback to default state on parse error. |
| Scaling issues on high DPI / fullscreen | Medium | Use responsive Qt layouts (`QSplitter`, `QHBoxLayout`, `QScrollArea`) with dynamic stretch factors rather than hardcoded pixels. |

# Tasks: py-cookie-clicker (Cosmic Asteroid Miner)

## Phase 1: Foundation & Domain Logic (TDD)

- [x] Task 1: Core Models & Economy Formulas (`src/models.py`, `tests/test_models.py`)
- [x] Task 2: Game Engine & Loop (`src/game_engine.py`, `tests/test_game_engine.py`)
- [x] Task 3: Savegame Manager & Serialization (`src/save_manager.py`, `tests/test_save_manager.py`)

## Checkpoint 1: Domain & Tests

- [x] Verify: `uv run pytest` all green
- [x] Verify: `uv run ruff check` clean

## Phase 2: Assets & Audio

- [x] Task 4: Generate visual PNG assets for Asteroid, Comet, and Structures (`src/assets/`)
- [x] Task 5: Sound Effects Generation & Audio Controller (`src/audio.py`, `tests/test_audio.py`)

## Phase 3: GUI Components & Presentation

- [x] Task 6: Interactive Asteroid & Comet Widget (`src/widgets/asteroid_widget.py`)
- [x] Task 7: Shop & Upgrades Panel (`src/widgets/shop_widget.py`)
- [x] Task 8: HUD, Statistics & Settings Dialog (`src/widgets/hud_widget.py`, `src/widgets/settings_dialog.py`)
- [x] Task 9: Assemble MainWindow, F11 Fullscreen, Sci-Fi QSS, and QSettings (`src/main.py`)

## Checkpoint 2: Integration & Verification

- [x] Full automated test suite passes (`uv run pytest`)
- [x] Code formatting & lint passes (`uv run ruff check`)
- [x] Manual launch verification of main game loop

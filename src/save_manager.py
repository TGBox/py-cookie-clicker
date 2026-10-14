"""Savegame persistence, serialization, atomic file writing, and export/import."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from src.models import GameState, create_default_game_state


def get_default_save_path() -> Path:
    """Return platform-appropriate persistent savegame path."""
    app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if app_data:
        save_dir = Path(app_data) / "py-cookie-clicker"
    else:
        save_dir = Path.home() / ".py-cookie-clicker"
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir / "savegame.json"


class SaveManager:
    """Handles JSON serialization, atomic writes, and string import/export."""

    def __init__(self, save_path: Path | None = None):
        self.save_path = save_path or get_default_save_path()

    def serialize(self, state: GameState) -> dict[str, Any]:
        """Convert GameState into a serializable dictionary."""
        return {
            "version": 1,
            "dust": state.dust,
            "lifetime_dust": state.lifetime_dust,
            "manual_clicks": state.manual_clicks,
            "comets_clicked": state.comets_clicked,
            "buildings": {b_id: b.count for b_id, b in state.buildings.items()},
            "upgrades": [u_id for u_id, u in state.upgrades.items() if u.purchased],
            "achievements": [a_id for a_id, a in state.achievements.items() if a.unlocked],
        }

    def deserialize(self, data: dict[str, Any]) -> GameState:
        """Hydrate GameState from dictionary, overlaying onto default template."""
        state = create_default_game_state()
        state.dust = float(data.get("dust", 0.0))
        state.lifetime_dust = float(data.get("lifetime_dust", 0.0))
        state.manual_clicks = int(data.get("manual_clicks", 0))
        state.comets_clicked = int(data.get("comets_clicked", 0))

        # Restore buildings
        saved_buildings = data.get("buildings", {})
        for b_id, count in saved_buildings.items():
            if b_id in state.buildings:
                state.buildings[b_id].count = int(count)

        # Restore upgrades
        saved_upgrades = set(data.get("upgrades", []))
        for u_id in saved_upgrades:
            if u_id in state.upgrades:
                state.upgrades[u_id].purchased = True

        # Restore achievements
        saved_achievements = set(data.get("achievements", []))
        for a_id in saved_achievements:
            if a_id in state.achievements:
                state.achievements[a_id].unlocked = True

        return state

    def save(self, state: GameState) -> bool:
        """Atomically write savegame to disk."""
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.save_path.with_suffix(".tmp")
            payload = json.dumps(self.serialize(state), indent=2)
            tmp_path.write_text(payload, encoding="utf-8")
            tmp_path.replace(self.save_path)
            return True
        except (OSError, ValueError, TypeError):
            return False

    def load(self) -> GameState:
        """Load savegame from disk, falling back to clean state on failure."""
        if not self.save_path.exists():
            return create_default_game_state()

        try:
            content = self.save_path.read_text(encoding="utf-8")
            data = json.loads(content)
            return self.deserialize(data)
        except (OSError, json.JSONDecodeError, ValueError, KeyError):
            # Fallback to default state on corrupted or invalid file
            return create_default_game_state()

    def export_to_string(self, state: GameState) -> str:
        """Export savegame as a compact base64-encoded string."""
        raw_json = json.dumps(self.serialize(state))
        return base64.b64encode(raw_json.encode("utf-8")).decode("ascii")

    def import_from_string(self, save_str: str) -> GameState | None:
        """Decode and import base64 string."""
        try:
            decoded = base64.b64decode(save_str.strip().encode("ascii")).decode("utf-8")
            data = json.loads(decoded)
            return self.deserialize(data)
        except (ValueError, KeyError, json.JSONDecodeError):
            return None

    def reset_save(self) -> GameState:
        """Delete savegame file and return fresh default state."""
        if self.save_path.exists():
            try:
                self.save_path.unlink()
            except OSError:
                pass
        return create_default_game_state()

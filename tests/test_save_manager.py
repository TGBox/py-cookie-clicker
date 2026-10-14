import tempfile
from pathlib import Path

from src.models import create_default_game_state
from src.save_manager import SaveManager


def test_save_and_load_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        save_file = Path(tmpdir) / "test_save.json"
        manager = SaveManager(save_path=save_file)

        state = create_default_game_state()
        state.dust = 12345.5
        state.lifetime_dust = 67890.0
        state.manual_clicks = 42
        state.buildings["drone"].count = 15
        state.upgrades["click_1"].purchased = True
        state.achievements["ach_click_1"].unlocked = True

        # Save
        assert manager.save(state) is True
        assert save_file.exists()

        # Load
        loaded_state = manager.load()
        assert loaded_state.dust == 12345.5
        assert loaded_state.lifetime_dust == 67890.0
        assert loaded_state.manual_clicks == 42
        assert loaded_state.buildings["drone"].count == 15
        assert loaded_state.upgrades["click_1"].purchased is True
        assert loaded_state.achievements["ach_click_1"].unlocked is True


def test_export_and_import_string():
    manager = SaveManager()
    state = create_default_game_state()
    state.dust = 999.0
    state.buildings["laser"].count = 3

    # Export string
    save_str = manager.export_to_string(state)
    assert isinstance(save_str, str)
    assert len(save_str) > 20

    # Import string
    imported_state = manager.import_from_string(save_str)
    assert imported_state is not None
    assert imported_state.dust == 999.0
    assert imported_state.buildings["laser"].count == 3


def test_corrupted_save_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        save_file = Path(tmpdir) / "corrupt.json"
        save_file.write_text("NOT_VALID_JSON{{{", encoding="utf-8")

        manager = SaveManager(save_path=save_file)
        # Should gracefully fall back to default game state instead of crashing
        state = manager.load()
        assert state is not None
        assert state.dust == 0.0
        assert len(state.buildings) >= 5

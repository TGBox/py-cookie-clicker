import os

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from src.game_engine import GameEngine
from src.main import MainWindow
from src.models import create_default_game_state
from src.save_manager import SaveManager
from src.widgets.asteroid_widget import AsteroidWidget
from src.widgets.settings_dialog import SettingsDialog


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_instantiation(qapp):
    window = MainWindow()
    assert window.windowTitle() == "Cosmic Asteroid Miner"
    assert window.centralWidget() is not None
    assert window.hud is not None
    assert window.asteroid_widget is not None
    assert window.shop_widget is not None

    # Test fullscreen toggle
    window.toggle_fullscreen()
    assert window.isFullScreen() is True
    window.toggle_fullscreen()
    assert window.isFullScreen() is False

    # Test asteroid click trigger
    gain, is_crit = window.engine.manual_click()
    window._on_asteroid_clicked(gain, is_crit)
    assert window.state.dust >= 1.0

    # Test buy building
    window.state.dust = 1000.0
    window._on_buy_building("drone", 1)
    assert window.state.buildings["drone"].count >= 1

    window.close()


def test_asteroid_widget_feedback(qapp):
    state = create_default_game_state()
    engine = GameEngine(state)
    widget = AsteroidWidget(engine)
    widget.resize(400, 400)

    # Trigger click feedback
    widget.trigger_click_feedback(5.0, False, QPointF(200, 200))
    assert len(widget.floating_texts) == 1
    assert widget.floating_texts[0].text == "+5"

    # Trigger critical click
    widget.trigger_click_feedback(50.0, True, QPointF(200, 200))
    assert len(widget.floating_texts) == 2
    assert "KRITISCH" in widget.floating_texts[1].text


def test_settings_dialog(qapp):
    state = create_default_game_state()
    save_manager = SaveManager()
    dlg = SettingsDialog(state, save_manager, sound_enabled=True)
    assert dlg.tabs.count() == 2
    dlg.close()

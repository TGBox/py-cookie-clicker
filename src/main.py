"""Cosmic Asteroid Miner - Main application entry point and window orchestration."""

from __future__ import annotations

import sys
import time

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.audio import AudioManager
from src.game_engine import GameEngine
from src.models import GameState
from src.save_manager import SaveManager
from src.widgets.asteroid_widget import AsteroidWidget
from src.widgets.hud_widget import HUDWidget
from src.widgets.settings_dialog import SettingsDialog
from src.widgets.shop_widget import ShopWidget

SCI_FI_STYLESHEET = """
QMainWindow, QWidget#CentralWidget {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QSplitter::handle {
    background-color: #1e293b;
    width: 2px;
}

QScrollBar:vertical {
    background: #0f172a;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #00e5ff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QPushButton {
    background: rgba(30, 41, 59, 0.8);
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton:hover {
    background: rgba(51, 65, 85, 0.9);
    border-color: #00e5ff;
    color: #ffffff;
}
QPushButton:pressed {
    background: #0284c7;
}

QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0f172a;
    border-radius: 6px;
}
QTabBar::tab {
    background: #0f172a;
    color: #94a3b8;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #1e293b;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #1e293b;
    color: #00e5ff;
    font-weight: bold;
    border-bottom: 2px solid #00e5ff;
}

QLineEdit {
    background: #0f172a;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
}
QLineEdit:focus {
    border: 1px solid #00e5ff;
}

QToolTip {
    background-color: #0f172a;
    color: #e2e8f0;
    border: 1px solid #00e5ff;
    padding: 6px;
    border-radius: 4px;
}
"""


class MainWindow(QMainWindow):
    """Main window hosting game loop, asteroid canvas, shop sidebar, and top status HUD."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosmic Asteroid Miner")
        self.resize(1100, 720)
        self.setMinimumSize(850, 550)

        # Persistence & audio
        self.save_manager = SaveManager()
        self.state: GameState = self.save_manager.load()
        self.engine = GameEngine(self.state)

        # Settings
        self.settings = QSettings("PyCookieClicker", "CosmicMiner")
        sound_enabled = self.settings.value("sound_enabled", True, type=bool)
        self.audio = AudioManager(enabled=sound_enabled)

        # Setup UI
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_timers()
        self._restore_window_state()

        # Connect engine events
        self.engine.on_achievement_unlocked.append(self._on_achievement_unlocked)
        self.engine.on_comet_spawned.append(lambda _: self.audio.play_comet())

    def _setup_ui(self) -> None:
        self.setStyleSheet(SCI_FI_STYLESHEET)

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top HUD
        self.hud = HUDWidget(central_widget)
        self.hud.set_sound_button_state(self.audio.enabled)
        self.hud.sound_toggled.connect(self._toggle_sound)
        self.hud.fullscreen_requested.connect(self.toggle_fullscreen)
        self.hud.stats_requested.connect(lambda: self._open_settings(0))
        self.hud.settings_requested.connect(lambda: self._open_settings(1))
        root_layout.addWidget(self.hud)

        # Main splitter (Asteroid on Left, Shop on Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: Interactive Asteroid Canvas
        self.asteroid_widget = AsteroidWidget(self.engine, splitter)
        self.asteroid_widget.asteroid_clicked.connect(self._on_asteroid_clicked)
        self.asteroid_widget.comet_clicked.connect(self._on_comet_clicked)
        splitter.addWidget(self.asteroid_widget)

        # Right: Shop & Upgrades
        self.shop_widget = ShopWidget(splitter)
        self.shop_widget.setMinimumWidth(380)
        self.shop_widget.building_bought.connect(self._on_buy_building)
        self.shop_widget.upgrade_bought.connect(self._on_buy_upgrade)
        splitter.addWidget(self.shop_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root_layout.addWidget(splitter, stretch=1)

    def _setup_shortcuts(self) -> None:
        # F11 toggles fullscreen
        f11_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        f11_shortcut.activated.connect(self.toggle_fullscreen)

        # Esc exits fullscreen if currently active
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self._on_escape_pressed)

    def _setup_timers(self) -> None:
        # 100ms game simulation tick
        self.last_tick_time = time.perf_counter()
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._on_engine_tick)
        self.tick_timer.start(100)

        # 30-second autosave timer
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(lambda: self.save_manager.save(self.state))
        self.autosave_timer.start(30000)

    def _on_engine_tick(self) -> None:
        now = time.perf_counter()
        dt = now - self.last_tick_time
        self.last_tick_time = now

        self.engine.tick(dt)

        # Update views
        self.hud.update_view(
            self.state,
            self.engine.frenzy_remaining,
            self.engine.frenzy_multiplier,
        )
        self.shop_widget.update_view(self.state)

    def _on_asteroid_clicked(self, gain: float, is_crit: bool) -> None:
        self.audio.play_click(crit=is_crit)
        self.hud.update_view(
            self.state,
            self.engine.frenzy_remaining,
            self.engine.frenzy_multiplier,
        )

    def _on_comet_clicked(self, reward: float) -> None:
        self.audio.play_comet()
        self.hud.update_view(
            self.state,
            self.engine.frenzy_remaining,
            self.engine.frenzy_multiplier,
        )

    def _on_buy_building(self, building_id: str, amount: int) -> None:
        if self.state.buy_building(building_id, amount):
            self.audio.play_buy()
            self.shop_widget.update_view(self.state)
            self.hud.update_view(
                self.state,
                self.engine.frenzy_remaining,
                self.engine.frenzy_multiplier,
            )

    def _on_buy_upgrade(self, upgrade_id: str) -> None:
        if self.state.buy_upgrade(upgrade_id):
            self.audio.play_buy()
            self.shop_widget.update_view(self.state)
            self.hud.update_view(
                self.state,
                self.engine.frenzy_remaining,
                self.engine.frenzy_multiplier,
            )

    def _on_achievement_unlocked(self, ach) -> None:
        self.audio.play_buy()
        # Non-intrusive status bar hint
        self.statusBar().showMessage(f"🏆 Errungenschaft freigeschaltet: {ach.name}!", 5000)

    def _toggle_sound(self) -> None:
        new_state = not self.audio.enabled
        self.audio.set_enabled(new_state)
        self.settings.setValue("sound_enabled", new_state)
        self.hud.set_sound_button_state(new_state)

    def toggle_fullscreen(self) -> None:
        """Toggle between windowed and fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_escape_pressed(self) -> None:
        if self.isFullScreen():
            self.showNormal()

    def _open_settings(self, initial_tab: int = 0) -> None:
        dlg = SettingsDialog(
            state=self.state,
            save_manager=self.save_manager,
            sound_enabled=self.audio.enabled,
            initial_tab=initial_tab,
            parent=self,
        )
        dlg.save_requested.connect(lambda: self.save_manager.save(self.state))
        dlg.sound_toggled.connect(lambda en: self._toggle_sound() if en != self.audio.enabled else None)
        dlg.reset_requested.connect(self._reset_game)
        dlg.save_imported.connect(self._import_game)
        dlg.exec()

    def _reset_game(self) -> None:
        self.state = self.save_manager.reset_save()
        self.engine = GameEngine(self.state)
        self.engine.on_achievement_unlocked.append(self._on_achievement_unlocked)
        self.engine.on_comet_spawned.append(lambda _: self.audio.play_comet())
        self.asteroid_widget.engine = self.engine
        self.shop_widget.update_view(self.state)
        self.hud.update_view(self.state, 0.0, 1.0)
        self.statusBar().showMessage("Spielstand zurückgesetzt.", 3000)

    def _import_game(self, save_str: str) -> None:
        imported = self.save_manager.import_from_string(save_str)
        if imported:
            self.state = imported
            self.save_manager.save(self.state)
            self.engine = GameEngine(self.state)
            self.engine.on_achievement_unlocked.append(self._on_achievement_unlocked)
            self.engine.on_comet_spawned.append(lambda _: self.audio.play_comet())
            self.asteroid_widget.engine = self.engine
            self.shop_widget.update_view(self.state)
            self.hud.update_view(self.state, 0.0, 1.0)
            self.statusBar().showMessage("Spielstand erfolgreich importiert!", 4000)
        else:
            QMessageBox.critical(self, "Fehler", "Der eingegebene Spielstand-String ist ungültig.")

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:
        """Persist window geometry and game state on exit."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.save_manager.save(self.state)
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Cosmic Asteroid Miner")
    app.setOrganizationName("PyCookieClicker")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
"""Top HUD banner displaying cosmic currency, passive generation rate, and active buffs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models import GameState
from src.utils import format_number


class HUDWidget(QFrame):
    """Top status bar with currency metrics, frenzy indicator, and action tool buttons."""

    stats_requested = Signal()
    settings_requested = Signal()
    fullscreen_requested = Signal()
    sound_toggled = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("HUDWidget")
        self.setStyleSheet(
            "QFrame#HUDWidget { background: rgba(15, 23, 42, 0.85); "
            "border-bottom: 1px solid rgba(0, 229, 255, 0.2); }"
        )
        self.assets_dir = Path(__file__).parent.parent / "assets"
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        # Currency icon & numbers
        curr_box = QHBoxLayout()
        curr_box.setSpacing(12)

        self.crystal_icon = QLabel()
        self.crystal_icon.setFixedSize(48, 48)
        self.crystal_icon.setScaledContents(True)
        crystal_img = self.assets_dir / "crystal.jpg"
        if crystal_img.exists():
            self.crystal_icon.setPixmap(QPixmap(str(crystal_img)))
        curr_box.addWidget(self.crystal_icon)

        text_vbox = QVBoxLayout()
        text_vbox.setSpacing(2)

        self.dust_label = QLabel("0 Sternenstaub")
        self.dust_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.dust_label.setStyleSheet("color: #00f0ff; letter-spacing: 0.5px;")
        text_vbox.addWidget(self.dust_label)

        rates_hbox = QHBoxLayout()
        rates_hbox.setSpacing(14)

        self.ops_label = QLabel("pro Sekunde: +0,0")
        self.ops_label.setFont(QFont("Segoe UI", 10))
        self.ops_label.setStyleSheet("color: #94a3b8;")
        rates_hbox.addWidget(self.ops_label)

        self.click_label = QLabel("pro Klick: +1,0")
        self.click_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.click_label.setStyleSheet("color: #38bdf8;")
        rates_hbox.addWidget(self.click_label)

        rates_hbox.addStretch()
        text_vbox.addLayout(rates_hbox)

        curr_box.addLayout(text_vbox)
        layout.addLayout(curr_box)

        # Frenzy boost notification pill
        self.frenzy_label = QLabel()
        self.frenzy_label.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff007f, stop:1 #ffaa00); "
            "color: #ffffff; font-weight: bold; border-radius: 12px; padding: 4px 14px; font-size: 11px;"
        )
        self.frenzy_label.setVisible(False)
        layout.addWidget(self.frenzy_label)

        layout.addStretch()

        # Action buttons on right
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.sound_btn = QPushButton("Ton: An")
        self.sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sound_btn.clicked.connect(self.sound_toggled.emit)
        btn_box.addWidget(self.sound_btn)

        self.stats_btn = QPushButton("Errungenschaften")
        self.stats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stats_btn.clicked.connect(self.stats_requested.emit)
        btn_box.addWidget(self.stats_btn)

        self.fullscreen_btn = QPushButton("Vollbild (F11)")
        self.fullscreen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)
        btn_box.addWidget(self.fullscreen_btn)

        self.settings_btn = QPushButton("Optionen")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        btn_box.addWidget(self.settings_btn)

        layout.addLayout(btn_box)

    def update_view(self, state: GameState, frenzy_remaining: float, frenzy_multiplier: float) -> None:
        """Update top bar indicators."""
        self.dust_label.setText(f"{format_number(state.dust)} Sternenstaub")
        effective_ops = state.total_ops() * (frenzy_multiplier if frenzy_remaining > 0 else 1.0)
        self.ops_label.setText(f"pro Sekunde: +{format_number(effective_ops)}")

        effective_click = state.click_power() * (frenzy_multiplier if frenzy_remaining > 0 else 1.0)
        self.click_label.setText(f"pro Klick: +{format_number(effective_click)}")

        if frenzy_remaining > 0:
            self.frenzy_label.setVisible(True)
            self.frenzy_label.setText(f"⚡ FRENZY: {frenzy_multiplier:.0f}x Produktion ({int(frenzy_remaining):02d}s)")
        else:
            self.frenzy_label.setVisible(False)

    def set_sound_button_state(self, enabled: bool) -> None:
        """Update text on the sound toggle button."""
        self.sound_btn.setText("Ton: An" if enabled else "Ton: Aus")

"""Settings, statistics, savegame export/import, and achievements dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models import GameState
from src.save_manager import SaveManager
from src.utils import format_number


class SettingsDialog(QDialog):
    """Dialog providing stats, achievements view, save persistence, and audio controls."""

    save_requested = Signal()
    reset_requested = Signal()
    save_imported = Signal(str)  # base64 save string
    sound_toggled = Signal(bool)

    def __init__(
        self,
        state: GameState,
        save_manager: SaveManager,
        sound_enabled: bool,
        initial_tab: int = 0,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.state = state
        self.save_manager = save_manager
        self.sound_enabled = sound_enabled

        self.setWindowTitle("Optionen & Errungenschaften")
        self.setMinimumSize(560, 480)
        self.resize(600, 520)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Achievements & Statistics
        self.stats_tab = QWidget()
        self._setup_stats_tab()
        self.tabs.addTab(self.stats_tab, "Errungenschaften & Statistik")

        # Tab 2: Savegame & Options
        self.options_tab = QWidget()
        self._setup_options_tab()
        self.tabs.addTab(self.options_tab, "Spielstand & Einstellungen")

        self.tabs.setCurrentIndex(initial_tab)

        # Close button at bottom
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _setup_stats_tab(self) -> None:
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Stats Card
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid #1e293b;")
        stats_vbox = QVBoxLayout(stats_frame)
        stats_vbox.setSpacing(6)

        total_buildings = sum(b.count for b in self.state.buildings.values())
        total_upgrades = sum(1 for u in self.state.upgrades.values() if u.purchased)

        stats_vbox.addWidget(QLabel(f"<b>Gesamter Sternenstaub abgebaut:</b> {format_number(self.state.lifetime_dust)}"))
        stats_vbox.addWidget(QLabel(f"<b>Manuelle Asteroiden-Klicks:</b> {self.state.manual_clicks:,d}"))
        stats_vbox.addWidget(QLabel(f"<b>Gefangene Kometen:</b> {self.state.comets_clicked}"))
        stats_vbox.addWidget(QLabel(f"<b>Aktive Flotten-Einheiten:</b> {total_buildings}"))
        stats_vbox.addWidget(QLabel(f"<b>Erforschte Upgrades:</b> {total_upgrades} / {len(self.state.upgrades)}"))
        layout.addWidget(stats_frame)

        # Achievements header
        ach_unlocked_count = sum(1 for a in self.state.achievements.values() if a.unlocked)
        ach_header = QLabel(f"ERRUNGENSCHAFTEN ({ach_unlocked_count} / {len(self.state.achievements)})")
        ach_header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ach_header.setStyleSheet("color: #e2e8f0; letter-spacing: 0.5px;")
        layout.addWidget(ach_header)

        # Achievements list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        ach_layout = QVBoxLayout(scroll_content)
        ach_layout.setSpacing(6)

        for ach in self.state.achievements.values():
            item = QFrame()
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(10, 8, 10, 8)

            badge = QLabel("🏆" if ach.unlocked else "🔒")
            badge.setFont(QFont("Segoe UI", 14))
            item_layout.addWidget(badge)

            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            name_lbl = QLabel(ach.name)
            name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            desc_lbl = QLabel(ach.description)
            desc_lbl.setStyleSheet("color: #8da2c0; font-size: 10px;")
            text_box.addWidget(name_lbl)
            text_box.addWidget(desc_lbl)
            item_layout.addLayout(text_box, stretch=1)

            status_lbl = QLabel("FREIGESCHALTET" if ach.unlocked else "GESPERRT")
            status_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            if ach.unlocked:
                status_lbl.setStyleSheet("color: #10b981;")
                item.setStyleSheet("background: rgba(16, 185, 129, 0.08); border-radius: 6px; border: 1px solid #059669;")
            else:
                status_lbl.setStyleSheet("color: #64748b;")
                item.setStyleSheet("background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid #1e293b;")
            item_layout.addWidget(status_lbl)

            ach_layout.addWidget(item)

        ach_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

    def _setup_options_tab(self) -> None:
        layout = QVBoxLayout(self.options_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Audio toggle
        sound_box = QFrame()
        sound_box.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid #1e293b;")
        sound_layout = QHBoxLayout(sound_box)
        self.sound_check = QCheckBox("Soundeffekte aktivieren")
        self.sound_check.setChecked(self.sound_enabled)
        self.sound_check.toggled.connect(self.sound_toggled.emit)
        sound_layout.addWidget(self.sound_check)
        layout.addWidget(sound_box)

        # Save actions
        save_box = QFrame()
        save_box.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid #1e293b;")
        save_layout = QVBoxLayout(save_box)
        save_layout.setSpacing(10)

        save_btn_row = QHBoxLayout()
        manual_save_btn = QPushButton("Jetzt Speichern")
        manual_save_btn.clicked.connect(self._on_manual_save)
        self.save_status_lbl = QLabel()
        self.save_status_lbl.setStyleSheet("color: #10b981; font-weight: bold;")
        save_btn_row.addWidget(manual_save_btn)
        save_btn_row.addWidget(self.save_status_lbl)
        save_btn_row.addStretch()
        save_layout.addLayout(save_btn_row)

        # Export string
        export_row = QHBoxLayout()
        self.export_line = QLineEdit()
        self.export_line.setReadOnly(True)
        self.export_line.setPlaceholderText("Spielstand exportieren...")
        copy_btn = QPushButton("Exportieren")
        copy_btn.clicked.connect(self._on_export)
        export_row.addWidget(self.export_line, stretch=1)
        export_row.addWidget(copy_btn)
        save_layout.addLayout(export_row)

        # Import string
        import_row = QHBoxLayout()
        self.import_line = QLineEdit()
        self.import_line.setPlaceholderText("Export-String hier einfügen...")
        import_btn = QPushButton("Importieren")
        import_btn.clicked.connect(self._on_import)
        import_row.addWidget(self.import_line, stretch=1)
        import_row.addWidget(import_btn)
        save_layout.addLayout(import_row)

        layout.addWidget(save_box)

        # Danger zone
        danger_box = QFrame()
        danger_box.setStyleSheet("background: rgba(239, 68, 68, 0.05); border-radius: 8px; border: 1px solid #dc2626;")
        danger_layout = QHBoxLayout(danger_box)
        reset_lbl = QLabel("Spielstand komplett auf Anfang zurücksetzen")
        reset_lbl.setStyleSheet("color: #fca5a5;")
        reset_btn = QPushButton("Zurücksetzen")
        reset_btn.setStyleSheet(
            "QPushButton { background: #dc2626; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px; } "
            "QPushButton:hover { background: #b91c1c; }"
        )
        reset_btn.clicked.connect(self._on_reset)
        danger_layout.addWidget(reset_lbl)
        danger_layout.addStretch()
        danger_layout.addWidget(reset_btn)
        layout.addWidget(danger_box)

        layout.addStretch()

    def _on_manual_save(self) -> None:
        self.save_requested.emit()
        self.save_status_lbl.setText("✓ Gespeichert!")

    def _on_export(self) -> None:
        save_str = self.save_manager.export_to_string(self.state)
        self.export_line.setText(save_str)
        QApplication.clipboard().setText(save_str)
        self.save_status_lbl.setText("✓ In Zwischenablage kopiert!")

    def _on_import(self) -> None:
        text = self.import_line.text().strip()
        if not text:
            return
        confirm = QMessageBox.question(
            self,
            "Spielstand importieren",
            "Möchtest du diesen Spielstand wirklich laden? Der aktuelle Fortschritt wird überschrieben.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.save_imported.emit(text)
            self.accept()

    def _on_reset(self) -> None:
        confirm = QMessageBox.warning(
            self,
            "Spielstand zurücksetzen",
            "Bist du absolut sicher? Dein gesamter Fortschritt wird unwiderruflich gelöscht!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.reset_requested.emit()
            self.accept()

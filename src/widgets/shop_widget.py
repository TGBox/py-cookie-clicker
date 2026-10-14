"""Shop and upgrades interface with bulk buy multipliers and reactive state updates."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.models import GameState
from src.utils import format_number


class BuildingRowWidget(QFrame):
    """Widget row representing an individual mineable structure in the shop."""

    buy_requested = Signal(str)  # building_id

    def __init__(self, building_id: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.building_id = building_id
        self.setObjectName("BuildingRow")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(44, 44)
        self.icon_label.setScaledContents(True)
        self.icon_label.setStyleSheet("border-radius: 6px; background: rgba(255,255,255,0.05);")
        layout.addWidget(self.icon_label)

        # Info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_row = QHBoxLayout()
        self.name_label = QLabel()
        self.name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(
            "background: rgba(0, 229, 255, 0.2); color: #00e5ff; font-weight: bold; "
            "padding: 2px 8px; border-radius: 10px; font-size: 11px;"
        )
        name_row.addWidget(self.name_label)
        name_row.addStretch()
        name_row.addWidget(self.count_badge)
        info_layout.addLayout(name_row)

        self.ops_label = QLabel()
        self.ops_label.setStyleSheet("color: #8da2c0; font-size: 11px;")
        info_layout.addWidget(self.ops_label)

        layout.addLayout(info_layout, stretch=1)

        # Buy button
        self.buy_btn = QPushButton()
        self.buy_btn.setMinimumWidth(110)
        self.buy_btn.setFixedHeight(38)
        self.buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.buy_btn.clicked.connect(lambda: self.buy_requested.emit(self.building_id))
        layout.addWidget(self.buy_btn)

    def update_view(self, state: GameState, multiplier_mode: str, assets_dir: Path) -> None:
        """Refresh contents based on current state and selected buy mode."""
        b = state.buildings.get(self.building_id)
        if not b:
            return

        # Load icon
        icon_path = assets_dir / "drone.jpg"  # default
        if icon_path.exists():
            self.icon_label.setPixmap(QPixmap(str(icon_path)))

        self.name_label.setText(b.name)
        self.count_badge.setText(str(b.count))

        # Calculate current OpS
        b_mult = 1.0
        for upg in state.upgrades.values():
            if upg.purchased and (
                upg.target_type == "global"
                or (upg.target_type == "building" and upg.target_id == b.id)
            ):
                b_mult *= upg.multiplier

        total_ops = b.total_ops(b_mult)
        self.ops_label.setText(f"{format_number(b.base_ops * b_mult)} OpS/Stk. • Gesamt: {format_number(total_ops)} OpS")

        # Amount to buy
        if multiplier_mode == "MAX":
            amount = max(1, state.max_affordable_buildings(b.id))
        else:
            amount = int(multiplier_mode)

        cost = b.current_cost(amount)
        can_afford = state.dust >= cost and amount > 0

        self.buy_btn.setText(f"+{amount}\n{format_number(cost)} ✦")
        self.buy_btn.setEnabled(can_afford)
        if can_afford:
            self.buy_btn.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0088cc, stop:1 #00b4d8); "
                "color: #ffffff; font-weight: bold; border-radius: 6px; border: 1px solid #48cae4; font-size: 11px; } "
                "QPushButton:hover { background: #00b4d8; }"
            )
        else:
            self.buy_btn.setStyleSheet(
                "QPushButton { background: rgba(255, 255, 255, 0.05); color: #556987; "
                "border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); font-size: 11px; }"
            )


class ShopWidget(QWidget):
    """Complete shop panel containing multiplier switches, upgrade shelf, and building list."""

    building_bought = Signal(str, int)  # building_id, amount
    upgrade_bought = Signal(str)  # upgrade_id

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.multiplier_mode = "1"
        self.assets_dir = Path(__file__).parent.parent / "assets"
        self.building_rows: dict[str, BuildingRowWidget] = {}

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # Header with title & buy multiplier buttons
        header_layout = QHBoxLayout()
        title_label = QLabel("TECHNOLOGIE & FLOTTE")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #e2e8f0; letter-spacing: 1px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Multiplier radio buttons
        self.mult_group = QButtonGroup(self)
        mult_layout = QHBoxLayout()
        mult_layout.setSpacing(4)
        for label_text in ["1", "10", "100", "MAX"]:
            rb = QPushButton(f"{label_text}x" if label_text != "MAX" else "MAX")
            rb.setCheckable(True)
            rb.setFixedSize(48, 28)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            if label_text == "1":
                rb.setChecked(True)
            rb.clicked.connect(lambda _, val=label_text: self._set_multiplier(val))
            self.mult_group.addButton(rb)
            mult_layout.addWidget(rb)
        header_layout.addLayout(mult_layout)
        main_layout.addLayout(header_layout)

        # Upgrades shelf section
        upg_box = QFrame()
        upg_box.setStyleSheet("background: rgba(15, 23, 42, 0.6); border-radius: 8px; border: 1px solid #1e293b;")
        upg_vbox = QVBoxLayout(upg_box)
        upg_vbox.setContentsMargins(10, 8, 10, 8)
        upg_title = QLabel("FORSCHUNG & UPGRADES")
        upg_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        upg_title.setStyleSheet("color: #94a3b8; font-size: 10px; letter-spacing: 0.5px;")
        upg_vbox.addWidget(upg_title)

        self.upgrades_layout = QHBoxLayout()
        self.upgrades_layout.setSpacing(8)
        upg_vbox.addLayout(self.upgrades_layout)
        main_layout.addWidget(upg_box)

        # Buildings scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.scroll_content = QWidget()
        self.buildings_layout = QVBoxLayout(self.scroll_content)
        self.buildings_layout.setContentsMargins(0, 0, 0, 0)
        self.buildings_layout.setSpacing(8)
        self.buildings_layout.addStretch()

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, stretch=1)

    def _set_multiplier(self, val: str) -> None:
        self.multiplier_mode = val

    def _on_buy_building(self, building_id: str, state: GameState) -> None:
        b = state.buildings.get(building_id)
        if not b:
            return
        if self.multiplier_mode == "MAX":
            amount = max(1, state.max_affordable_buildings(b.id))
        else:
            amount = int(self.multiplier_mode)
        self.building_bought.emit(building_id, amount)

    def update_view(self, state: GameState) -> None:
        """Update all building rows and available upgrades."""
        # 1. Update or create building rows
        for b_id in state.buildings:
            if b_id not in self.building_rows:
                row = BuildingRowWidget(b_id, self.scroll_content)
                row.buy_requested.connect(lambda b_id=b_id: self._on_buy_building(b_id, state))
                self.building_rows[b_id] = row
                # Insert before stretch
                self.buildings_layout.insertWidget(self.buildings_layout.count() - 1, row)
            self.building_rows[b_id].update_view(state, self.multiplier_mode, self.assets_dir)

        # 2. Update upgrade buttons in shelf
        # Clear existing upgrade buttons
        while self.upgrades_layout.count() > 0:
            item = self.upgrades_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Find available unpurchased upgrades that are unlocked
        available_upgrades = [
            u
            for u in state.upgrades.values()
            if not u.purchased and state.lifetime_dust >= u.unlock_threshold
        ]

        if not available_upgrades:
            no_upg_lbl = QLabel("Keine weiteren Upgrades verfügbar")
            no_upg_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
            self.upgrades_layout.addWidget(no_upg_lbl)
        else:
            for upg in available_upgrades[:6]:  # Show top 6 available
                can_afford = state.dust >= upg.cost
                btn = QPushButton()
                btn.setFixedSize(54, 54)
                btn.setCursor(Qt.CursorShape.PointingHandCursor if can_afford else Qt.CursorShape.ForbiddenCursor)
                btn.setToolTip(f"<b>{upg.name}</b><br>{upg.description}<br><br><b>Kosten: {format_number(upg.cost)} ✦</b>")
                btn.setText("★\n" + format_number(upg.cost))
                if can_afford:
                    btn.setStyleSheet(
                        "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7928ca, stop:1 #4338ca); "
                        "color: #ffffff; border-radius: 8px; border: 1px solid #c084fc; font-size: 9px; font-weight: bold; } "
                        "QPushButton:hover { border: 2px solid #f43f5e; }"
                    )
                else:
                    btn.setStyleSheet(
                        "QPushButton { background: rgba(255, 255, 255, 0.05); color: #64748b; "
                        "border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); font-size: 9px; }"
                    )
                btn.clicked.connect(lambda _, u_id=upg.id: self.upgrade_bought.emit(u_id))
                self.upgrades_layout.addWidget(btn)
        self.upgrades_layout.addStretch()

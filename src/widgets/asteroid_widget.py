"""Interactive asteroid viewport with click feedback, floating text particles, and comets."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from src.game_engine import GameEngine


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: QColor
    alpha: float = 1.0
    vy: float = -2.2
    scale: float = 1.0


class AsteroidWidget(QWidget):
    """Custom widget rendering the interactive central asteroid, floating numbers, and golden comets."""

    asteroid_clicked = Signal(float, bool)  # gain, is_crit
    comet_clicked = Signal(float)  # reward

    def __init__(self, engine: GameEngine, parent: QWidget | None = None):
        super().__init__(parent)
        self.engine = engine
        self.setMinimumSize(360, 360)
        self.setMouseTracking(True)

        # Visual assets
        assets_dir = Path(__file__).parent.parent / "assets"
        self.asteroid_pixmap = QPixmap(str(assets_dir / "asteroid.jpg"))
        self.comet_pixmap = QPixmap(str(assets_dir / "comet.jpg"))

        # Animation states
        self.scale_factor = 1.0
        self.target_scale = 1.0
        self.floating_texts: list[FloatingText] = []
        self.comet_rect: QRectF | None = None
        self.comet_pulse = 0.0

        # Background stars for atmospheric depth
        self.stars = [
            (random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(1.0, 2.5), random.uniform(0.3, 0.9))
            for _ in range(40)
        ]

        # 60 FPS animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(16)

    def trigger_click_feedback(self, gain: float, is_crit: bool, click_pos: QPointF | None = None) -> None:
        """Add floating gain text and animate scale squeeze."""
        self.scale_factor = 0.93  # Click squeeze
        pos = click_pos or QPointF(self.width() / 2, self.height() / 2)

        # Slight random scatter
        sx = pos.x() + random.uniform(-25, 25)
        sy = pos.y() + random.uniform(-15, 10)

        from src.utils import format_number

        formatted_gain = format_number(gain)
        if is_crit:
            text = f"+{formatted_gain} KRITISCH!"
            color = QColor(255, 215, 0)  # Bright gold
            scale = 1.3
        else:
            text = f"+{formatted_gain}"
            color = QColor(0, 240, 255)  # Neon cyan
            scale = 1.0

        self.floating_texts.append(FloatingText(x=sx, y=sy, text=text, color=color, scale=scale))

    def _update_animation(self) -> None:
        """Advance animation states for scale recovery, comets, and floating text."""
        # Scale interpolation
        if abs(self.scale_factor - self.target_scale) > 0.001:
            self.scale_factor += (self.target_scale - self.scale_factor) * 0.2
        else:
            self.scale_factor = self.target_scale

        # Comet pulse
        self.comet_pulse += 0.08
        if self.comet_pulse > math.tau:
            self.comet_pulse -= math.tau

        # Update floating texts
        retained: list[FloatingText] = []
        for ft in self.floating_texts:
            ft.y += ft.vy
            ft.alpha -= 0.02
            if ft.alpha > 0:
                retained.append(ft)
        self.floating_texts = retained

        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle clicks on either golden comet or the central asteroid."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            # Check if clicked on active comet
            if self.comet_rect and self.comet_rect.contains(pos):
                reward = self.engine.click_comet()
                from src.utils import format_number

                self.floating_texts.append(
                    FloatingText(
                        x=pos.x(),
                        y=pos.y(),
                        text=f"+{format_number(reward)} KOMETEN-BONUS!",
                        color=QColor(255, 220, 60),
                        scale=1.5,
                    )
                )
                self.comet_clicked.emit(reward)
                return

            # Clicked asteroid
            gain, is_crit = self.engine.manual_click()
            self.trigger_click_feedback(gain, is_crit, pos)
            self.asteroid_clicked.emit(gain, is_crit)

    def paintEvent(self, event) -> None:
        """Render stars, glowing halo, asteroid, comets, and floating texts."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # 1. Background dark space fill
        painter.fillRect(0, 0, w, h, QColor(10, 14, 26))

        # 2. Distant stars
        for sx, sy, size, alpha in self.stars:
            star_color = QColor(200, 230, 255, int(alpha * 255))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(star_color)
            painter.drawEllipse(QPointF(sx * w, sy * h), size, size)

        # 3. Asteroid
        center_x = w / 2
        center_y = h / 2
        asteroid_size = min(w, h) * 0.65 * self.scale_factor

        if not self.asteroid_pixmap.isNull():
            # Glowing backdrop aura
            aura_radius = asteroid_size * 0.6
            glow_color = QColor(0, 180, 255, 35)
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(center_x, center_y), aura_radius, aura_radius)

            target_rect = QRectF(
                center_x - asteroid_size / 2,
                center_y - asteroid_size / 2,
                asteroid_size,
                asteroid_size,
            )
            # Clip as circular or rounded mask for the asteroid
            painter.save()
            from PySide6.QtGui import QPainterPath

            path = QPainterPath()
            path.addEllipse(target_rect)
            painter.setClipPath(path)
            painter.drawPixmap(target_rect.toRect(), self.asteroid_pixmap)
            painter.restore()

        # 4. Active Golden Comet
        if self.engine.active_comet:
            comet = self.engine.active_comet
            cx = comet.x * w
            cy = comet.y * h
            pulse_scale = 1.0 + 0.15 * math.sin(self.comet_pulse)
            comet_size = 64.0 * pulse_scale

            self.comet_rect = QRectF(cx - comet_size / 2, cy - comet_size / 2, comet_size, comet_size)

            # Comet glow
            glow = QColor(255, 180, 20, 60)
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy), comet_size * 0.7, comet_size * 0.7)

            if not self.comet_pixmap.isNull():
                painter.drawPixmap(self.comet_rect.toRect(), self.comet_pixmap)
        else:
            self.comet_rect = None

        # 5. Floating text numbers
        for ft in self.floating_texts:
            painter.save()
            font = QFont("Segoe UI", int(14 * ft.scale), QFont.Weight.Bold)
            painter.setFont(font)
            color = QColor(ft.color)
            color.setAlphaF(max(0.0, min(1.0, ft.alpha)))
            painter.setPen(color)

            # Draw text centered on position
            painter.drawText(int(ft.x - 60), int(ft.y), 120, 30, Qt.AlignmentFlag.AlignCenter, ft.text)
            painter.restore()

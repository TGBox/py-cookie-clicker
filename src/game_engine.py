"""Core game loop engine, comet mechanics, and event dispatch."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from src.models import Achievement, GameState


@dataclass
class GoldenComet:
    x: float  # Normalized coordinates 0.0 - 1.0
    y: float
    duration: float = 12.0
    reward_dust: float = 100.0
    is_frenzy: bool = False
    frenzy_duration: float = 10.0
    frenzy_multiplier: float = 7.0


class GameEngine:
    """Orchestrates continuous time ticks, passive income, random events, and achievements."""

    def __init__(self, state: GameState):
        self.state = state
        self.active_comet: GoldenComet | None = None
        self.comet_timer: float = 0.0
        self.next_comet_interval: float = self._get_next_comet_interval()

        self.frenzy_remaining: float = 0.0
        self.frenzy_multiplier: float = 1.0

        # Event listeners
        self.on_tick: list[Callable[[GameState], None]] = []
        self.on_achievement_unlocked: list[Callable[[Achievement], None]] = []
        self.on_comet_spawned: list[Callable[[GoldenComet], None]] = []
        self.on_comet_expired: list[Callable[[], None]] = []

    def _get_next_comet_interval(self) -> float:
        """Random interval between comets: between 45 and 120 seconds."""
        return random.uniform(45.0, 120.0)

    def activate_frenzy(self, duration: float = 10.0, multiplier: float = 7.0) -> None:
        """Activate temporary frenzy boost."""
        self.frenzy_remaining = duration
        self.frenzy_multiplier = multiplier

    def manual_click(self) -> tuple[float, bool]:
        """Perform a manual click on the asteroid.
        
        Returns:
            tuple[float, bool]: (dust_gained, is_critical_hit)
        """
        # 5% chance of critical hit (10x gain)
        is_crit = random.random() < 0.05
        multiplier = 10.0 if is_crit else 1.0
        if self.frenzy_remaining > 0:
            multiplier *= self.frenzy_multiplier

        gain = self.state.add_manual_click(multiplier)
        self.check_achievements()
        return gain, is_crit

    def click_comet(self) -> float:
        """Catch active golden comet and award bonus."""
        if not self.active_comet:
            return 0.0

        comet = self.active_comet
        self.active_comet = None
        self.state.comets_clicked += 1

        reward = comet.reward_dust
        self.state.dust += reward
        self.state.lifetime_dust += reward

        if comet.is_frenzy:
            self.activate_frenzy(comet.frenzy_duration, comet.frenzy_multiplier)

        self.check_achievements()
        return reward

    def tick(self, dt: float) -> None:
        """Advance game simulation by `dt` seconds."""
        if dt <= 0:
            return

        # Handle Frenzy countdown
        effective_frenzy = 1.0
        if self.frenzy_remaining > 0:
            effective_frenzy = self.frenzy_multiplier
            self.frenzy_remaining = max(0.0, self.frenzy_remaining - dt)
            if self.frenzy_remaining == 0.0:
                self.frenzy_multiplier = 1.0

        # Passive dust generation
        base_ops = self.state.total_ops()
        generated = base_ops * effective_frenzy * dt
        self.state.dust += generated
        self.state.lifetime_dust += generated

        # Comet lifecycle
        if self.active_comet:
            self.active_comet.duration -= dt
            if self.active_comet.duration <= 0:
                self.active_comet = None
                for cb in self.on_comet_expired:
                    cb()
        else:
            self.comet_timer += dt
            if self.comet_timer >= self.next_comet_interval:
                self.spawn_comet()

        # Check achievements
        self.check_achievements()

        # Notify tick listeners
        for cb in self.on_tick:
            cb(self.state)

    def spawn_comet(self) -> None:
        """Spawn a new golden comet."""
        self.comet_timer = 0.0
        self.next_comet_interval = self._get_next_comet_interval()

        # Reward scales with current OpS or click power
        ops = self.state.total_ops()
        reward = max(100.0, ops * 30.0)  # At least 30s of OpS
        is_frenzy = random.random() < 0.40  # 40% chance of frenzy

        comet = GoldenComet(
            x=random.uniform(0.1, 0.9),
            y=random.uniform(0.1, 0.8),
            duration=12.0,
            reward_dust=reward,
            is_frenzy=is_frenzy,
        )
        self.active_comet = comet
        for cb in self.on_comet_spawned:
            cb(comet)

    def check_achievements(self) -> None:
        """Evaluate criteria for locked achievements."""
        for ach in self.state.achievements.values():
            if ach.unlocked:
                continue

            unlocked = False
            if ach.condition_type == "clicks":
                if self.state.manual_clicks >= ach.threshold:
                    unlocked = True
            elif ach.condition_type == "total_dust":
                if self.state.lifetime_dust >= ach.threshold:
                    unlocked = True
            elif ach.condition_type == "building_count" and ach.target_id:
                b = self.state.buildings.get(ach.target_id)
                if b and b.count >= ach.threshold:
                    unlocked = True
            elif (
                ach.condition_type == "comets"
                and self.state.comets_clicked >= ach.threshold
            ):
                unlocked = True

            if unlocked:
                ach.unlocked = True
                for cb in self.on_achievement_unlocked:
                    cb(ach)

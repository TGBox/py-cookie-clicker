"""Domain models and economy formulas for Cosmic Asteroid Miner."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Building:
    id: str
    name: str
    description: str
    base_cost: float
    base_ops: float
    count: int = 0
    cost_multiplier: float = 1.15
    icon_name: str = "drone.png"

    def current_cost(self, amount: int = 1) -> float:
        """Calculate total cost to purchase `amount` buildings using geometric progression."""
        if amount <= 0:
            return 0.0
        if amount == 1:
            return round(self.base_cost * (self.cost_multiplier**self.count), 2)
        # Sum of geometric series: base_cost * multiplier^count * (multiplier^amount - 1) / (multiplier - 1)
        r = self.cost_multiplier
        c = self.count
        total = self.base_cost * (r**c) * ((r**amount) - 1.0) / (r - 1.0)
        return round(total, 2)

    def total_ops(self, multiplier: float = 1.0) -> float:
        """Calculate total ore/dust production per second from this building type."""
        return self.count * self.base_ops * multiplier


@dataclass
class Upgrade:
    id: str
    name: str
    description: str
    cost: float
    target_type: str  # "click", "building", "global"
    multiplier: float
    target_id: str | None = None
    purchased: bool = False
    unlock_threshold: float = 0.0
    icon_name: str = "upgrade.png"


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    condition_type: str  # "clicks", "total_dust", "building_count", "comets"
    threshold: float
    target_id: str | None = None
    unlocked: bool = False
    icon_name: str = "trophy.png"


@dataclass
class GameState:
    dust: float = 0.0
    lifetime_dust: float = 0.0
    manual_clicks: int = 0
    comets_clicked: int = 0
    buildings: dict[str, Building] = field(default_factory=dict)
    upgrades: dict[str, Upgrade] = field(default_factory=dict)
    achievements: dict[str, Achievement] = field(default_factory=dict)

    def click_power(self) -> float:
        """Compute current dust gained per manual click."""
        power = 1.0
        # Check click upgrades
        for upg in self.upgrades.values():
            if upg.purchased and upg.target_type == "click":
                power *= upg.multiplier
        # Global upgrades also affect clicks
        for upg in self.upgrades.values():
            if upg.purchased and upg.target_type == "global":
                power *= upg.multiplier
        return power

    def total_ops(self) -> float:
        """Compute current passive dust production per second."""
        total = 0.0
        global_multiplier = 1.0
        for upg in self.upgrades.values():
            if upg.purchased and upg.target_type == "global":
                global_multiplier *= upg.multiplier

        for b_id, b in self.buildings.items():
            b_mult = global_multiplier
            for upg in self.upgrades.values():
                if upg.purchased and upg.target_type == "building" and upg.target_id == b_id:
                    b_mult *= upg.multiplier
            total += b.total_ops(b_mult)
        return total

    def add_manual_click(self, multiplier: float = 1.0) -> float:
        """Perform a click, updating dust and stats."""
        gain = self.click_power() * multiplier
        self.dust += gain
        self.lifetime_dust += gain
        self.manual_clicks += 1
        return gain

    def max_affordable_buildings(self, building_id: str) -> int:
        """Calculate maximum quantity of a building that can be bought with current dust."""
        b = self.buildings.get(building_id)
        if not b or self.dust < b.current_cost(1):
            return 0
        r = b.cost_multiplier
        c = b.count
        # Solve: base_cost * r^c * (r^n - 1) / (r - 1) <= dust
        val = 1.0 + (self.dust * (r - 1.0)) / (b.base_cost * (r**c))
        if val <= 1.0:
            return 0
        n = math.floor(math.log(val, r))
        return max(0, n)

    def buy_building(self, building_id: str, amount: int = 1) -> bool:
        """Attempt to buy buildings."""
        b = self.buildings.get(building_id)
        if not b:
            return False
        cost = b.current_cost(amount)
        if self.dust >= cost and amount > 0:
            self.dust -= cost
            b.count += amount
            return True
        return False

    def buy_upgrade(self, upgrade_id: str) -> bool:
        """Attempt to purchase an upgrade."""
        u = self.upgrades.get(upgrade_id)
        if not u or u.purchased:
            return False
        if self.dust >= u.cost:
            self.dust -= u.cost
            u.purchased = True
            return True
        return False


def create_default_game_state() -> GameState:
    """Create a fully seeded new game state with all space buildings and upgrades."""
    state = GameState()

    # Space buildings
    default_buildings = [
        Building("drone", "Mining-Drohne", "Kompakte Drohne sammelt Mineralpartikel", 15.0, 0.5, icon_name="drone.png"),
        Building("laser", "Plasma-Bohrer", "Hochenergetischer Laser schmilzt Erzadern", 100.0, 4.0, icon_name="laser.png"),
        Building("rover", "Schwerer Abbau-Rover", "Geländegängiger Rover auf der Asteroidenoberfläche", 1100.0, 32.0, icon_name="rover.png"),
        Building("drill", "Tiefbohr-Plattform", "Bohrt bis in den Kern metallischer Asteroiden", 12000.0, 260.0, icon_name="drill.png"),
        Building("station", "Orbitale Station", "Raumstation zur automatischen Erzverarbeitung", 130000.0, 1400.0, icon_name="station.png"),
        Building("refinery", "Raffinerie-Schiff", "Mobiles Großraumschiff schmilzt ganze Planetoiden", 1400000.0, 7800.0, icon_name="refinery.png"),
        Building("dyson", "Dyson-Schwarm", "Solare Kollektoren speisen kosmische Abbauanlagen", 20000000.0, 44000.0, icon_name="dyson.png"),
        Building("antimatter", "Antimaterie-Ernter", "Subatomare Ernte verdichtet pure Raumenergie", 330000000.0, 260000.0, icon_name="antimatter.png"),
    ]
    for b in default_buildings:
        state.buildings[b.id] = b

    # Upgrades
    default_upgrades = [
        # Click upgrades
        Upgrade("click_1", "Diamant-Bohrspitze", "Verdoppelt manuellen Klick-Ertrag", 100.0, "click", 2.0, unlock_threshold=50.0),
        Upgrade("click_2", "Ionen-Verstärker", "Verdoppelt manuellen Klick-Ertrag", 500.0, "click", 2.0, unlock_threshold=250.0),
        Upgrade("click_3", "Quanten-Resonator", "Verdreifacht manuellen Klick-Ertrag", 10000.0, "click", 3.0, unlock_threshold=5000.0),
        # Drone upgrades
        Upgrade("drone_1", "Optimierte Rotoren", "Mining-Drohnen sind doppelt so effizient", 150.0, "building", 2.0, target_id="drone", unlock_threshold=100.0),
        Upgrade("drone_2", "Schwarm-Intelligenz", "Mining-Drohnen sind doppelt so effizient", 1500.0, "building", 2.0, target_id="drone", unlock_threshold=1000.0),
        # Laser upgrades
        Upgrade("laser_1", "Rubin-Fokuslinse", "Plasma-Bohrer erzielen 2x Ausbeute", 1000.0, "building", 2.0, target_id="laser", unlock_threshold=500.0),
        Upgrade("laser_2", "Überladene Kondensatoren", "Plasma-Bohrer erzielen 2x Ausbeute", 10000.0, "building", 2.0, target_id="laser", unlock_threshold=5000.0),
        # Rover upgrades
        Upgrade("rover_1", "Titan-Ketten", "Abbau-Rover sind 2x so effizient", 12000.0, "building", 2.0, target_id="rover", unlock_threshold=6000.0),
        # Global upgrades
        Upgrade("global_1", "Galaktische Handelsrouten", "Erhöht gesamte Produktion um 10%", 50000.0, "global", 1.10, unlock_threshold=25000.0),
        Upgrade("global_2", "KI-Mining-Protokoll", "Erhöht gesamte Produktion um 20%", 500000.0, "global", 1.20, unlock_threshold=250000.0),
    ]
    for u in default_upgrades:
        state.upgrades[u.id] = u

    # Achievements
    default_achievements = [
        Achievement("ach_click_1", "Erster Hammerschlag", "Klicke den Asteroiden 1 Mal", "clicks", 1.0),
        Achievement("ach_click_100", "Unermüdlicher Bergmann", "Klicke den Asteroiden 100 Mal", "clicks", 100.0),
        Achievement("ach_click_1000", "Klick-Virtuose", "Klicke den Asteroiden 1.000 Mal", "clicks", 1000.0),
        Achievement("ach_dust_1000", "Erste Tonne", "Sammle insgesamt 1.000 Sternenstaub", "total_dust", 1000.0),
        Achievement("ach_dust_1m", "Millionär der Sterne", "Sammle insgesamt 1.000.000 Sternenstaub", "total_dust", 1000000.0),
        Achievement("ach_drones_10", "Drohnenschwarm", "Besitze mindestens 10 Mining-Drohnen", "building_count", 10.0, target_id="drone"),
        Achievement("ach_dyson_1", "Meister der Sonne", "Baue deinen ersten Dyson-Schwarm", "building_count", 1.0, target_id="dyson"),
        Achievement("ach_comet_1", "Glücklicher Komet", "Fange deinen ersten goldenen Kometen", "comets", 1.0),
    ]
    for a in default_achievements:
        state.achievements[a.id] = a

    return state

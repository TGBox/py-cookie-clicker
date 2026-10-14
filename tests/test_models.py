from src.models import (
    Building,
    Upgrade,
    create_default_game_state,
)


def test_building_cost_calculation():
    drone = Building(
        id="drone",
        name="Mining-Drohne",
        description="Autonome Bergbau-Drohne",
        base_cost=15.0,
        base_ops=0.5,
        count=0,
    )
    assert drone.current_cost() == 15.0
    drone.count = 1
    assert drone.current_cost() == 17.25  # 15 * 1.15^1


def test_building_bulk_cost_calculation():
    drone = Building(
        id="drone",
        name="Mining-Drohne",
        description="Autonome Bergbau-Drohne",
        base_cost=10.0,
        base_ops=1.0,
        count=0,
        cost_multiplier=1.15,
    )
    # Buy 1: 10
    assert drone.current_cost(1) == 10.0
    # Buy 2 from 0: 10 + 11.5 = 21.5
    assert round(drone.current_cost(2), 2) == 21.5


def test_game_state_initial_values():
    state = create_default_game_state()
    assert state.dust == 0.0
    assert state.lifetime_dust == 0.0
    assert state.manual_clicks == 0
    assert state.click_power() == 1.0
    assert state.total_ops() == 0.0
    assert len(state.buildings) >= 5
    assert len(state.upgrades) >= 5
    assert len(state.achievements) >= 5


def test_game_state_click_and_upgrades():
    state = create_default_game_state()
    # Click 1 time
    state.add_manual_click()
    assert state.dust == 1.0
    assert state.lifetime_dust == 1.0
    assert state.manual_clicks == 1

    # Apply click upgrade
    click_upg = Upgrade(
        id="iron_pick",
        name="Titan-Bohrspitze",
        description="Verdoppelt Klick-Ertrag",
        cost=10.0,
        target_type="click",
        multiplier=2.0,
        purchased=True,
    )
    state.upgrades["iron_pick"] = click_upg
    assert state.click_power() == 2.0

    # Add flat click bonus
    flat_upg = Upgrade(
        id="gloves",
        name="Plasma-Handschuhe",
        description="+5 pro Klick",
        cost=20.0,
        target_type="click_flat",
        multiplier=5.0,
        purchased=True,
    )
    state.upgrades["gloves"] = flat_upg
    # Base 1 + 5 = 6, times 2 = 12
    assert state.click_power() == 12.0

    # Add % of OpS to click
    state.buildings["drone"].count = 100  # 50 OpS
    ops_percent_upg = Upgrade(
        id="resonance",
        name="Kinetische Resonanz",
        description="+2% des OpS zu jedem Klick",
        cost=50.0,
        target_type="click_ops_percent",
        multiplier=0.02,
        purchased=True,
    )
    state.upgrades["resonance"] = ops_percent_upg
    # 50 OpS * 0.02 = 1.0. Total before mult: 6 + 1 = 7. Multiplied by 2 = 14.
    assert state.click_power() == 14.0


def test_game_state_building_ops():
    state = create_default_game_state()
    state.buildings["drone"].count = 4  # base_ops = 0.5 -> 2.0 OpS
    assert state.total_ops() == 2.0

    # Add 2x building upgrade
    drone_upg = Upgrade(
        id="drone_boost",
        name="Turbo-Triebwerke",
        description="Drohnen bauen doppelt so schnell ab",
        cost=50.0,
        target_type="building",
        target_id="drone",
        multiplier=2.0,
        purchased=True,
    )
    state.upgrades["drone_boost"] = drone_upg
    assert state.total_ops() == 4.0


def test_max_affordable_and_buy_building():
    state = create_default_game_state()
    state.dust = 100.0
    # Drone base cost is 15.0 with multiplier 1.15
    # 1: 15.0, 2: 17.25, 3: 19.8375, 4: 22.813125, 5: 26.23509375 -> sum of 5 is 101.13 > 100
    # sum of 4 is 74.90 <= 100
    max_drones = state.max_affordable_buildings("drone")
    assert max_drones == 4

    # Buy 4 drones
    cost = state.buildings["drone"].current_cost(4)
    success = state.buy_building("drone", 4)
    assert success is True
    assert state.buildings["drone"].count == 4
    assert round(state.dust, 2) == round(100.0 - cost, 2)

    # Buy upgrade
    state.dust = 200.0
    upg_success = state.buy_upgrade("click_1")
    assert upg_success is True
    assert state.upgrades["click_1"].purchased is True
    assert state.dust == 100.0


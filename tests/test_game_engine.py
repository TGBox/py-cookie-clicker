from src.game_engine import GameEngine, GoldenComet
from src.models import create_default_game_state


def test_engine_passive_tick():
    state = create_default_game_state()
    engine = GameEngine(state)
    state.buildings["drone"].count = 2  # 1.0 OpS
    # Tick 1.5 seconds
    engine.tick(1.5)
    assert round(state.dust, 2) == 1.5
    assert round(state.lifetime_dust, 2) == 1.5


def test_engine_achievement_unlock():
    state = create_default_game_state()
    engine = GameEngine(state)
    unlocked_names = []
    engine.on_achievement_unlocked.append(lambda ach: unlocked_names.append(ach.id))

    # Click once -> should unlock "ach_click_1"
    engine.manual_click()
    assert "ach_click_1" in unlocked_names
    assert state.achievements["ach_click_1"].unlocked is True


def test_engine_comet_spawn_and_click():
    state = create_default_game_state()
    engine = GameEngine(state)
    comet = GoldenComet(x=0.5, y=0.5, duration=10.0, reward_dust=500.0)
    engine.active_comet = comet

    initial_dust = state.dust
    reward = engine.click_comet()
    assert reward == 500.0
    assert state.dust == initial_dust + 500.0
    assert state.comets_clicked == 1
    assert engine.active_comet is None
    # Check comet achievement
    assert state.achievements["ach_comet_1"].unlocked is True


def test_engine_frenzy_multiplier():
    state = create_default_game_state()
    engine = GameEngine(state)
    state.buildings["laser"].count = 1  # 4 OpS
    engine.activate_frenzy(duration=10.0, multiplier=7.0)

    # 1 second tick under 7x frenzy
    engine.tick(1.0)
    assert round(state.dust, 2) == 28.0  # 4 * 7 * 1.0
    assert round(engine.frenzy_remaining, 1) == 9.0

    # Advance beyond frenzy duration
    engine.tick(10.0)
    assert engine.frenzy_remaining == 0.0
    # After frenzy finishes, next 1 second should produce base 4 OpS
    current_dust = state.dust
    engine.tick(1.0)
    assert round(state.dust - current_dust, 2) == 4.0

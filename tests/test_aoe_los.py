import pytest
from gameplay import aoe_los as mod

CASES = [
    ("blocked", 'm.los_blocked(True) is True'),
    ("layers", 'm.layer_count([True, False, True]) == 2'),
    ("cover", 'm.cover_attenuation(10.0, 0.5) == approx(5.0)'),
    ("friendly", 'm.friendly_fire("a", "b") is True'),
    ("same_team", 'm.friendly_fire("a", "a") is False'),
    ("fallback", 'm.fallback_center((0.0, 0.0), None) == (0.0, 0.0)'),
    ("server", 'm.server_authority(1, 2) == 2'),
    ("dynamic", 'm.dynamic_query(False, True) is True'),
    ("cap", 'm.stack_cap(10.0, 5.0) == approx(5.0)'),
    ("ray", 'm.multi_ray_score([True, False]) == approx(0.5)'),
    ("material", 'm.material_factor(10.0, 0.5) == approx(5.0)'),
    ("grid", 'm.grid_dedupe([1, 1, 2]) == 2'),
    ("lag", 'm.lag_state(1, 2) == 2'),
    ("idem", 'm.event_idempotent(1, [2, 3]) is True'),
    ("idem_false", 'm.event_idempotent(2, [2, 3]) is False')
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx})

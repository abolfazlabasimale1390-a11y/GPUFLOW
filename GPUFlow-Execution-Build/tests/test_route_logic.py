from app.main import decide_route


def test_simple_auto_routes_lightweight():
    assert decide_route("Hello", "auto")["tier"] == "Lightweight"


def test_long_or_demanding_prompt_routes_advanced():
    assert decide_route("Please research the architecture of this system", "auto")["tier"] == "Advanced"


def test_manual_mode_is_respected():
    assert decide_route("Hello", "balanced")["tier"] == "Balanced"

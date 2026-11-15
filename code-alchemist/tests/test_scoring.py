from simulation import new_mission, advance_day
from scoring import calculate_mission_score


def test_score_structure():
    m = new_mission("Moon", 3, 10, "standard")
    for _ in range(5):
        m = advance_day(m, None)
    result = calculate_mission_score(m)
    assert "score" in result
    assert "grade" in result
    assert "breakdown" in result
    assert "lessons" in result
    assert 0 <= result["score"] <= 100

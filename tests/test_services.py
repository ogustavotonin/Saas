from app.services import calculate_bonus_and_points


def test_calculate_bonus_and_points_when_sale_closed():
    bonus, points = calculate_bonus_and_points(True, 3600, 5)
    assert bonus == 180.0
    assert points == 36


def test_calculate_bonus_and_points_when_sale_not_closed():
    bonus, points = calculate_bonus_and_points(False, 3600, 5)
    assert bonus == 0.0
    assert points == 30

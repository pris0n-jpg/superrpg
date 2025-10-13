import sys
import os
import random

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from world.tools import (
    WORLD,
    attack_roll_dnd,
    get_position,
    roll_dice,
    set_dnd_character,
    set_position,
)


def test_set_and_get_position():
    res1 = set_position("Tester", 2, 3)
    meta = res1.metadata or {}
    assert meta.get("position") == [2, 3]
    res2 = get_position("Tester")
    assert res2.metadata.get("position") == [2, 3]


def test_stat_block_and_attack():
    # Deterministic randomness
    random.seed(42)
    set_dnd_character(
        name="A",
        level=1,
        ac=12,
        abilities={"STR": 12, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
        proficient_skills=["athletics"],
        proficient_saves=["STR"],
        move_speed=6,
    )
    set_dnd_character(
        name="B",
        level=1,
        ac=10,
        abilities={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
    )
    set_position("A", 0, 0)
    set_position("B", 0, 1)
    res = attack_roll_dnd("A", "B", ability="STR", proficient=True, damage_expr="1d4+STR")
    assert "攻击" in (res.content or [{}])[0].get("text", "")
    # hp should be <= max after damage applied
    hp_after = WORLD.characters["B"]["hp"]
    assert 0 <= hp_after <= WORLD.characters["B"]["max_hp"]
    assert res.metadata.get("reach_ok") is True


def test_roll_dice_parse_and_total():
    random.seed(123)
    out = roll_dice("2d6+1")
    total = out.metadata.get("total")
    assert isinstance(total, int)
    assert 3 <= total <= 13


def test_attack_respects_reach_without_auto_move():
    random.seed(1)
    set_dnd_character(
        name="A",
        level=1,
        ac=12,
        abilities={"STR": 12, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
        move_speed=6,
    )
    set_dnd_character(
        name="B",
        level=1,
        ac=10,
        abilities={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
    )
    set_position("A", 0, 0)
    set_position("B", 0, 4)

    res = attack_roll_dnd("A", "B", ability="STR", proficient=True, damage_expr="1d4+STR")
    assert res.metadata.get("reach_ok") is False
    assert WORLD.positions["A"] == (0, 0)


def test_attack_auto_move_into_reach():
    random.seed(3)
    set_dnd_character(
        name="A",
        level=1,
        ac=12,
        abilities={"STR": 12, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
        move_speed=6,
    )
    set_dnd_character(
        name="B",
        level=1,
        ac=10,
        abilities={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
    )
    set_position("A", 0, 0)
    set_position("B", 0, 3)

    res = attack_roll_dnd(
        "A",
        "B",
        ability="STR",
        proficient=True,
        damage_expr="1d4+STR",
        auto_move=True,
    )
    assert res.metadata.get("reach_ok") is True
    auto_meta = res.metadata.get("auto_move") or {}
    assert auto_meta.get("ok") is True
    assert WORLD.positions["A"] != (0, 0)
    assert auto_meta.get("distance_after") <= auto_meta.get("reach_steps")


def test_attack_auto_move_fails_when_speed_short():
    set_dnd_character(
        name="Slow",
        level=1,
        ac=12,
        abilities={"STR": 12, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
        move_speed=1,
    )
    set_dnd_character(
        name="Target",
        level=1,
        ac=10,
        abilities={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        max_hp=10,
    )
    set_position("Slow", 0, 0)
    set_position("Target", 0, 3)

    res = attack_roll_dnd(
        "Slow",
        "Target",
        ability="STR",
        proficient=True,
        damage_expr="1d4+STR",
        auto_move=True,
    )
    assert res.metadata.get("reach_ok") is False
    auto_meta = res.metadata.get("auto_move") or {}
    assert auto_meta.get("ok") is False
    # Slow should have advanced but still remains out of reach
    assert WORLD.positions["Slow"] != (0, 0)

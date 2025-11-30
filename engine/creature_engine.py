from models import LivingEntity


class Creature(LivingEntity):
    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level

    def combat_stats(self):
        base_hp = 100
        base_attack = 5
        hp_growth = 12
        atk_growth = 3

        return {
            "hp": base_hp + (self.level - 1) * hp_growth,
            "attack": base_attack + (self.level - 1) * atk_growth,
        }


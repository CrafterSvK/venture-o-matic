import random
import re

from models import Character


class FightEngine:
    def calculate_damage_verbose(self, atk: dict, df: dict):
        chance_to_hit = 0.85 + atk.get("accuracy", 0) * 0.005
        if random.random() > chance_to_hit:
            return 0, False, False

        damage = atk.get("attack", 1) - df.get("defense", 0) * 0.4
        if damage < 1:
            damage = 1

        crit = random.random() < atk.get("crit_chance", 0)
        if crit:
            damage *= 1.5

        return round(damage, 2), True, crit

    def resolve_duel(self, a: Character, b: Character):
        stats_a = a.combat_stats()
        stats_b = b.combat_stats()

        hp_a = stats_a["hp"]
        hp_b = stats_b["hp"]

        log = []
        log.append(f"⚔️ [1;2m{a.name}[0m vs [1;2m{b.name}[0m — the duel begins!")

        attacker, defender = a, b
        atk_stats, def_stats = stats_a, stats_b

        round_num = 1

        while hp_a > 0 and hp_b > 0:
            log.append(f"")
            log.append(f"**Round {round_num}**")

            damage, hit, crit = self.calculate_damage_verbose(atk_stats, def_stats)

            hp_b_before = hp_b
            hp_a_before = hp_a

            if hit:
                if attacker is a:
                    hp_b -= damage
                else:
                    hp_a -= damage

                if crit:
                    text = f"➡️ {attacker.name} hits {defender.name} for [1;2m[1;31m{damage}[0m[0m damage"
                else:
                    text = f"➡️ {attacker.name} hits {defender.name} for [1;2m{damage}[0m damage"

                log.append(text)
            else:
                log.append(f"❌ {attacker.name} missed!")

            hp_line = f"❤️ {a.name}: {hp_a_before:.2f} HP | ❤️ {b.name}: {hp_b_before:.2f} HP"
            log.append(hp_line)

            if defender is a:
                dmg_part = f"(-{damage:.2f})"
                p = hp_line.find("HP") - len(dmg_part)
                dmg_log = (" " * p) + dmg_part
            else:
                dmg_part = f"(-{damage:.2f})"
                p = hp_line.rfind("HP") - len(dmg_part)
                dmg_log = (" " * p) + dmg_part

            log.append(dmg_log)

            n_a = len(str(int(hp_a_before))) - len(str(int(hp_a)))
            n_b = len(str(int(hp_b_before))) - len(str(int(hp_b)))

            if defender is a:
                finish_line = f"❤️ {a.name}: {" " * n_a}{hp_a:.2f} HP | ❤️ {b.name}: {hp_b:.2f} HP"
            else:
                finish_line = f"❤️ {a.name}: {hp_a:.2f} HP | ❤️ {b.name}: {" " * n_b}{hp_b:.2f} HP"

            log.append(finish_line)

            if hp_a <= 0 or hp_b <= 0:
                break

            attacker, defender = defender, attacker
            atk_stats, def_stats = def_stats, atk_stats
            round_num += 1

        winner = a if hp_a > 0 else b
        loser  = b if hp_a > 0 else a

        log.append("")
        log.append(f"🏆 {winner.name} wins the duel!")

        return winner, loser, log

from loader import DATA

def calculate_stats(character, equipment_rows):
    final_stats = {}

    for eq in equipment_rows:
        item = DATA.items.items.get(eq.item_id)
        if not item or "base_stats" not in item:
            continue

        for stat, value in item.base_stats.items():
            final_stats[stat] = final_stats.get(stat, 0) + value

    return final_stats

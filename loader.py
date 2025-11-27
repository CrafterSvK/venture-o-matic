from typing import Any

import yaml
import random
import os

from jsonschema import validate
from pydantic import BaseModel

from generated.items_types import ItemTemplates


class GameData(BaseModel):
    items: ItemTemplates
    shops: dict[str, Any]
    crafting: dict[str, Any]
    professions: dict[str, Any]
    affixes: dict[str, Any]
    rarity_rolls: dict[str, Any]


DATA: GameData
I18N = {}


def load_yaml(path, schema=None):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if schema:
        validate(data, schema)

    return data


def load_all_data():
    base = "data"

    items_schema = load_yaml(os.path.join("schemas", "items.schema.json"))

    global DATA
    DATA = GameData(
        items=ItemTemplates.model_validate(load_yaml(os.path.join(base, "items.yaml"), items_schema)),
        shops=load_yaml(os.path.join(base, "shops.yaml")),
        crafting=load_yaml(os.path.join(base, "crafting.yaml")),
        professions=load_yaml(os.path.join(base, "professions.yaml")),
        affixes=load_yaml(os.path.join(base, "affixes.yaml")),
        rarity_rolls=load_yaml(os.path.join(base, "rarity_rolls.yaml")),
    )
    return DATA


def load_translations(language="en"):
    global I18N
    lang_file = f"locales/{language}.yaml"
    I18N = load_yaml(lang_file)
    return I18N


def t(key: str, **kwargs):
    """
    Example: t("shop.not_found")
    """
    parts = key.split(".")
    node = I18N
    for p in parts:
        node = node.get(p, {})
    if isinstance(node, str):
        return node.format(**kwargs)
    return "MISSING_TRANSLATION"


def weighted_choice(weights: dict):
    total = sum(weights.values())
    r = random.uniform(0, total)
    upto = 0
    for k, w in weights.items():
        if upto + w >= r:
            return k
        upto += w
    return k

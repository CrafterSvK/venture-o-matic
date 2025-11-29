from typing import Any

import jsonschema
import yaml
import random
import os

from jsonschema import validate, RefResolver
from pydantic import BaseModel, ValidationError

from generated.character_schema import CharacterData
from generated.items_schema import ItemTemplates


class GameData(BaseModel):
    items: ItemTemplates
    character: CharacterData
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
    schema_dir = "schemas"

    items_schema = os.path.join(schema_dir, "items.schema.yaml")
    character_schema = os.path.join(schema_dir, "character.schema.yaml")

    global DATA
    DATA = GameData(
        items=ItemTemplates.model_validate(
            load_and_validate(
                os.path.join(base, "items.yaml"),
                items_schema,
                schema_dir,
            )
        ),
        character=CharacterData.model_validate(
            load_and_validate(
                os.path.join(base, "character.yaml"),
                character_schema,
                schema_dir,
            )
        ),
        shops=load_yaml(os.path.join(base, "shops.yaml")),
        crafting=load_yaml(os.path.join(base, "crafting.yaml")),
        professions=load_yaml(os.path.join(base, "professions.yaml")),
        affixes=load_yaml(os.path.join(base, "affixes.yaml")),
        rarity_rolls=load_yaml(os.path.join(base, "rarity_rolls.yaml")),
    )
    return DATA

class YamlResolver(RefResolver):
    def resolve_remote(self, uri):
        path = uri.removeprefix("file://")
        try:
            with open(path, "r") as f:
                print(f"🔎 Loading referenced schema: {path}")
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Referenced schema not found: {path}")
        except Exception as e:
            raise ValueError(f"❌ Failed to load referenced schema '{path}': {e}")


class SchemaValidationError(Exception):
    pass


def load_and_validate(data_path: str, schema_path: str, base_schema_dir: str = "schemas"):
    data_path = os.path.abspath(data_path)
    schema_path = os.path.abspath(schema_path)
    base_schema_dir = os.path.abspath(base_schema_dir)

    try:
        with open(data_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise SchemaValidationError(
            f"\n❌ Failed to load YAML data:\n"
            f"   File: {data_path}\n"
            f"   Error: {e}"
        )

    try:
        with open(schema_path, "r") as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        raise SchemaValidationError(
            f"\n❌ Failed to load YAML schema:\n"
            f"   File: {schema_path}\n"
            f"   Error: {e}"
        )

    # Configure resolver
    base_uri = f"file://{base_schema_dir}/"
    resolver = YamlResolver(base_uri=base_uri, referrer=schema)

    try:
        jsonschema.validate(data, schema, resolver=resolver)
    except ValidationError as ve:
        raise SchemaValidationError(
            f"\n❌ SCHEMA VALIDATION FAILED\n"
            f"   Schema file: {schema_path}\n"
            f"   Data file:   {data_path}\n"
            f"   Message:     {ve.message}\n"
            f"   Path:        {'/'.join(str(p) for p in ve.path)}\n"
            f"   Schema path: {'/'.join(str(p) for p in ve.schema_path)}\n"
        )
    except Exception as e:
        raise SchemaValidationError(
            f"\n❌ INTERNAL SCHEMA ERROR\n"
            f"   While validating: {data_path}\n"
            f"   Schema: {schema_path}\n"
            f"   Error: {e}\n"
            f"   (Likely a broken $ref, missing file, or invalid schema)\n"
        )

    return data

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
    return f"*{key}*"


def weighted_choice(weights: dict):
    total = sum(weights.values())
    r = random.uniform(0, total)
    upto = 0
    for k, w in weights.items():
        if upto + w >= r:
            return k
        upto += w
    return k

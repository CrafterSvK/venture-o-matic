from dataclasses import dataclass

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

import json

from loader import t

class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column()
    gold: Mapped[int] = mapped_column(default=0)
    level: Mapped[int] = mapped_column(default=1)
    xp: Mapped[int] = mapped_column(default=0)
    location: Mapped[str] = mapped_column(default="spawn")

    inventory: Mapped[list["Inventory"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )

    item_instances: Mapped[list["ItemInstance"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    equipment: Mapped[list["EquippedItem"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )

    professions: Mapped[list["CharacterProfession"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )

    def combat_stats(self):
        # Base stats
        result = {
            "hp": 100,
            "attack": 5,
            "defense": 0,
            "crit_chance": 0.01,
            "accuracy": 0,
        }

        # Add level scaling (optional)
        result["hp"] += (self.level - 1) * 5
        result["attack"] += (self.level - 1) * 1

        # Add equipment stats
        for e in self.equipment:
            inst_stats = json.loads(e.item_instance.rolled_stats)

            for k, v in inst_stats.items():
                result[k] = result.get(k, 0) + v

        return result



class Inventory(Base):
    """
    Stackable items (crafting materials, etc.)
    """
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    template_id: Mapped[str] = mapped_column(String(50))
    amount: Mapped[int] = mapped_column(default=0)

    character: Mapped["Character"] = relationship(back_populates="inventory")

    def __str__(self):
        return f"{self.amount}x {t(f'item.{self.template_id}')}"


class ItemInstance(Base):
    """
    Instancable non-stackable items (weapons, armor, etc.)
    """
    __tablename__ = "item_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)

    template_id: Mapped[str] = mapped_column(String(50), comment="Item template id")
    rarity: Mapped[str] = mapped_column(String(30), comment="Rarity of the item")
    rolled_stats: Mapped[str] = mapped_column(String, comment="JSON stats rolled on creation")
    affixes: Mapped[str] = mapped_column(String, comment="Affixes applied to the item, JSON")

    # MARKETPLACE
    is_listed: Mapped[bool] = mapped_column(default=False, comment="Is listed on marketplace?")
    list_price: Mapped[int] = mapped_column(default=0, comment="Price listed on marketplace")

    owner: Mapped["Character"] = relationship(back_populates="item_instances")

    def name(self):
        base_name = t(f"item.{self.template_id}")
        affix_data = json.loads(self.affixes) if self.affixes else {"prefixes": [], "suffixes": []}
        def fix_affix(a):
            return a.replace("_", " ").title()
        prefixes = [fix_affix(a) for a in affix_data.get("prefixes", [])]
        suffixes = [fix_affix(a) for a in affix_data.get("suffixes", [])]
        return " ".join(prefixes + [base_name] + suffixes)

    def __str__(self):
        rarity_styles = {
            "common": ("", "```text\n{n}\n{s}```"), # white
            "uncommon":  ("ansi", """
```ansi
[2;32m{n}[0m\n{s}!
```
"""), # green
            "rare": ("ansi", """
```ansi
[2;34m{n}[0m\n{s}!
```
"""), # blue
            "epic": ("ansi", """
```ansi
[2;31m{n}[0m\n{s}!
```
"""), # red
            "legendary": ("ansi", """
```ansi
[2;33m{n}[0m\n{s}!
```
"""), # yellow
        }

        style = rarity_styles.get(self.rarity, rarity_styles["common"])[1]

        return style.format(n=self.name(), s=json.loads(self.rolled_stats))


class EquippedItem(Base):
    """
    Equipped instancable item
    """
    __tablename__ = "equipped_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    slot: Mapped[str] = mapped_column(String(30))  # napr. "weapon", "chest"
    item_instance_id: Mapped[int] = mapped_column(
        ForeignKey("item_instances.id"),
        index=True,
    )

    character: Mapped["Character"] = relationship(back_populates="equipment")
    item_instance: Mapped["ItemInstance"] = relationship()


class CharacterProfession(Base):
    """
    Profession of a character
    """
    __tablename__ = "character_professions"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    profession_id: Mapped[str] = mapped_column(String(50))  # napr. "blacksmith"

    character: Mapped["Character"] = relationship(back_populates="professions")

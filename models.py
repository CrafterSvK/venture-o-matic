from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean


class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column()
    gold: Mapped[int] = mapped_column(default=0)

    # stackovateľné itemy (materiály atď.)
    inventory: Mapped[list["Inventory"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )

    # jednotlivé instancie itemov (equipment, craftnuté zbrane atď.)
    item_instances: Mapped[list["ItemInstance"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    # equipnuté itemy – referencujú ItemInstance
    equipment: Mapped[list["EquippedItem"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )

    # naučené profesie
    professions: Mapped[list["CharacterProfession"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )


class Inventory(Base):
    """
    Stackovateľné veci (podľa template_id z YAML) – napr. wood, iron_ore...
    """
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    template_id: Mapped[str] = mapped_column(String(50))  # napr. "wood", "iron_ore"
    amount: Mapped[int] = mapped_column(default=0)

    character: Mapped["Character"] = relationship(back_populates="inventory")


class ItemInstance(Base):
    """
    Konkrétna inštancia itemu – má rarity, affixy, konkrétne pre-rolované staty.
    Používa sa hlavne na equipovateľné veci, dropy, market…
    """
    __tablename__ = "item_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)

    # ID šablóny z YAML – napr. "iron_sword", "steel_sword"
    template_id: Mapped[str] = mapped_column(String(50))

    rarity: Mapped[str] = mapped_column(String(30))

    # JSON string – napr. {"attack": 12.5, "crit_chance": 0.04}
    rolled_stats: Mapped[str] = mapped_column(String)

    # JSON string – napr. {"prefixes": ["deadly"], "suffixes": ["of_the_wolf"]}
    affixes: Mapped[str] = mapped_column(String)

    # marketplace stav
    is_listed: Mapped[bool] = mapped_column(default=False)
    list_price: Mapped[int] = mapped_column(default=0)

    owner: Mapped["Character"] = relationship(back_populates="item_instances")


class EquippedItem(Base):
    """
    Aký ItemInstance je equipnutý v ktorom slote.
    """
    __tablename__ = "equipped_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    slot: Mapped[str] = mapped_column(String(30))          # napr. "weapon", "chest"
    item_instance_id: Mapped[int] = mapped_column(
        ForeignKey("item_instances.id"),
        index=True,
    )

    character: Mapped["Character"] = relationship(back_populates="equipment")
    item_instance: Mapped["ItemInstance"] = relationship()


class CharacterProfession(Base):
    """
    Naučené profesie – link postava <-> profesia (ID z YAML).
    """
    __tablename__ = "character_professions"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    profession_id: Mapped[str] = mapped_column(String(50))  # napr. "blacksmith"

    character: Mapped["Character"] = relationship(back_populates="professions")

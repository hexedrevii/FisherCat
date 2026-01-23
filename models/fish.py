from models.rarity import Rarity
from models.area import Area


class Fish:
  def __init__(self, id: int, name: str, rarity: Rarity, odds: int, area: Area, base_value: int):
    self.id = id

    self.name = name
    self.rarity = rarity
    self.odds = odds
    self.area = area
    self.base_value = base_value

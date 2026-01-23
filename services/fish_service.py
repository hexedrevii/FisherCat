from models.area import Area
from util.weighted_random import WeightedRandom


class FishService:
  def __init__(self):
    self.fish = []

    for area in Area:
      setattr(self, area.name, WeightedRandom())

import random
import bisect

from typing import Any

class WeightedRandom:
  def __init__(self):
    self.items = []
    self.cummulative_weight = []
    self.total_weight = 0


  def add(self, item: Any, weight: int) -> None:
    if weight <= 0:
      raise ValueError('weight must be positive.')

    self.items.append(item)
    self.total_weight += weight

    self.cummulative_weight.append(self.total_weight)


  def get(self) -> Any:
    if not self.items: return None

    rnd_point = random.uniform(0, self.total_weight)
    idx = bisect.bisect_right(self.cummulative_weight, rnd_point)

    return self.items[idx]

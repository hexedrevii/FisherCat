class Rod:
  def __init__(self, id: int, name: str, description: str, value: int, level_required: int, xp_multiplier: float, max_catch: int, min_catch: int, line_break_chance: int):
    self.id: int = id
    self.name: str = name
    self.description: str = description

    self.value: int = value
    self.level_required: int = level_required
    self.xp_multiplier: float = xp_multiplier

    self.max_catch: int = max_catch
    self.min_catch: int = min_catch

    self.line_break_chance: int = line_break_chance

class Rod:
  def __init__(self, id: int, name: str, value: int, internal_name: str, max_catch: int, min_catch: int, line_break_chance: int):
    self.id: int = id
    self.name: str = name

    self.value: int = value

    self.max_catch: int = max_catch
    self.min_catch: int = min_catch

    self.line_break_chance: int = line_break_chance

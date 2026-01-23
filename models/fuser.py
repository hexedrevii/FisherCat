import datetime
from datetime import datetime


class FUser:
    def __init__(self):
        self.coins: int = 0

        self.xp: int = 0
        self.xp_step: int = 1
        self.xp_next: int = 30

        self.level: int = 1

        self.lastclaimed: datetime = datetime.strptime('1970-01-01 02:00:00', '%Y-%m-%d %H:%M:%S')

        self.fishing_cooldown: int = 15

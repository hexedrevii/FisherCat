import sqlite3
import math
import logging
from typing import List, Tuple
from datetime import datetime

from models.area import Area
from models.fish import Fish
from models.fuser import FUser
from models.rarity import Rarity
from models.rod import Rod

LOGGER = logging.getLogger('FisherCat.DbService')


class DbService:
  def __init__(self, connection: sqlite3.Connection):
    self.connection = connection

    self.DAILY_BONUS_COINS = 500
    self.DAILY_XP_BONUS = 100

    self.LEVEL_INCREASE: float = 0.15
    self.LEVEL_GAP: float = 1.7

    self.COIN_REWARD: int = 50
    self.COIN_REWARD_INCREASE: float = 12.7

  def ensure_guild(self, guild_id: int) -> None:
    """
    Enrolls a guild in the database.
    """
    cursor = self.connection.cursor()

    # Check if the guild is already there.
    guild_exists = cursor.execute(
      'SELECT 1 FROM guild WHERE id = ?', (guild_id,)
    ).fetchone()
    if guild_exists:
      return

    with self.connection:
      cursor.execute('INSERT OR IGNORE INTO guild (id) VALUES (?)', (guild_id,))
      LOGGER.info(f'Enrolled guild: {guild_id}')

  def ensure_user(self, member_id: int, guild_id: int) -> FUser:
    """
    Add user to the database if not already present.
    """
    cursor = self.connection.cursor()

    result = cursor.execute(
      """
      SELECT * FROM guildmember WHERE guildid = ? AND memberid = ?;
    """,
      (guild_id, member_id),
    ).fetchone()

    if result is not None:
      # User exists, fill up the fuser and return.
      db_user = FUser()
      db_user.coins = result['coins']
      db_user.xp = result['xp']
      db_user.xp_step = result['xpstep']
      db_user.xp_next = result['xpnext']
      db_user.level = result['level']
      db_user.lastclaimed = datetime.strptime(
        result['lastclaimed'], '%Y-%m-%d %H:%M:%S'
      )
      db_user.fishing_cooldown = result['fishingcooldown']
      return db_user

    # User does not exist, enroll them.
    with self.connection:
      cursor.execute('INSERT INTO member (id) VALUES (?);', (member_id,))
      cursor.execute(
        """
          INSERT INTO guildmember (guildid, memberid) VALUES (?, ?)
          ON CONFLICT DO NOTHING;
        """,
        (guild_id, member_id),
      )

      cursor.execute(
        """
        INSERT OR IGNORE INTO memberrod (guildid, memberid, rodid) VALUES (?, ?, ?)
      """,
        (guild_id, member_id, 1),
      )

    return FUser()

  def add_xp(
    self, guild_id: int, member_id: int, xp: int, user: FUser
  ) -> Tuple[int, int]:
    user.xp += xp
    total_coins = 0
    total_levels = 0

    if user.xp >= user.xp_next:
      while user.xp >= user.xp_next:
        user.xp -= user.xp_next
        total_levels += 1
        user.level += 1

        reward = math.floor(self.COIN_REWARD + (user.level * self.COIN_REWARD_INCREASE))
        total_coins += reward
        user.coins += reward

        if user.xp_next != 5:
          if user.level % 10 == 0:
            user.xp_step += 1

        user.xp_next = math.floor(
          math.pow(user.level / self.LEVEL_INCREASE, self.LEVEL_GAP)
        )

    self.update_user(guild_id=guild_id, member_id=member_id, user=user)
    return (total_levels, total_coins)

  def add_fish(
    self, guild_id: int, member_id: int, fish_id: int, fish_amount: int = 1
  ) -> None:
    """
    Update player inventory with new fish.
    """
    with self.connection:
      self.connection.execute(
        f"""
        INSERT INTO inventory (guildid, memberid, fishid, amount) VALUES (?, ?, ?, ?)
        ON CONFLICT(guildid, memberid, fishid) DO UPDATE SET amount = amount + {fish_amount};
      """,
        (guild_id, member_id, fish_id, fish_amount),
      )

  def get_all_user_fish(self, guild_id: int, member_id: int) -> List[Tuple[Fish, int]]:
    """
    Returns a list of tuples, containing the fish on the left and the amount of it on the right.
    """
    cursor = self.connection.cursor()
    cursor.execute(
      """
      SELECT i.amount, f.* FROM inventory i
      JOIN fish f ON i.fishid = f.id
      WHERE i.guildid = ? AND i.memberid = ?;
    """,
      (guild_id, member_id),
    )

    rows = cursor.fetchall()
    fish_data: List[Tuple[Fish, int]] = []

    for row in rows:
      fish = Fish(
        id=row['id'],
        name=row['name'],
        xp=row['xp'],
        rarity=Rarity[row['rarity']],
        odds=row['odds'],
        area=Area[row['area']],
        base_value=row['base_value'],
      )
      fish_data.append((fish, row['amount']))

    return fish_data

  def get_user_fish(
    self, guild_id: int, member_id: int, fish_id: int
  ) -> Tuple[Fish, int]:
    cursor = self.connection.cursor()
    cursor.execute(
      """
      SELECT i.amount, f.* FROM inventory i
      INNER JOIN fish f ON i.fishid = f.id
      WHERE i.memberid = ? AND i.guildid = ? AND i.fishid = ?;
    """,
      (member_id, guild_id, fish_id),
    )

    row = cursor.fetchone()

    fish = Fish(
      id=row['id'],
      name=row['name'],
      xp=row['xp'],
      rarity=Rarity[row['rarity']],
      odds=row['odds'],
      area=Area[row['area']],
      base_value=row['base_value'],
    )
    return (fish, int(row['amount']))

  def update_user_fish(
    self, member_id: int, guild_id: int, fish_id: int, count: int
  ) -> None:
    with self.connection:
      if count <= 0:
        self.connection.execute(
          """
          DELETE FROM inventory
          WHERE fishid = ? AND memberid = ? AND guildid = ?
        """,
          (fish_id, member_id, guild_id),
        )
      else:
        self.connection.execute(
          """
          UPDATE inventory
          SET amount = ?
          WHERE fishid = ? AND memberid = ? AND guildid = ?;
        """,
          (count, fish_id, member_id, guild_id),
        )

  def get_user_rod(self, member_id: int, guild_id: int) -> Rod:
    cursor = self.connection.cursor()
    query = """
      SELECT
        r.id, r.name, r.description, r.value, r.levelrequired,
        r.xpmultiplier, r.mincatch, r.maxcatch, r.linebreakchance
      FROM guildmember gm
      JOIN rod r ON gm.rodid = r.id
      WHERE gm.memberid = ? AND gm.guildid = ?
    """
    cursor.execute(query, (member_id, guild_id))
    dbrod = cursor.fetchone()

    return Rod(
      id=dbrod['id'],
      name=dbrod['name'],
      description=dbrod['description'],
      value=dbrod['value'],
      level_required=dbrod['levelrequired'],
      xp_multiplier=dbrod['xpmultiplier'],
      min_catch=dbrod['mincatch'],
      max_catch=dbrod['maxcatch'],
      line_break_chance=dbrod['linebreakchance'],
    )

  def get_user_rods(self, member_id: int, guild_id: int) -> List[Rod]:
    cursor = self.connection.cursor()

    cursor.execute(
      """
        SELECT
        m.memberid, m.guildid, m.rodid,
        r.id, r.name, r.description, r.value, r.levelrequired, r.xpmultiplier, r.mincatch, r.maxcatch, r.linebreakchance
        FROM memberrod m
        JOIN rod r ON m.rodid = r.id
        WHERE m.guildid = ? AND m.memberid = ?;
      """,
      (guild_id, member_id),
    )

    rows = cursor.fetchall()
    data = []

    for dbrod in rows:
      data.append(
        Rod(
          id=dbrod['id'],
          name=dbrod['name'],
          description=dbrod['description'],
          value=dbrod['value'],
          level_required=dbrod['levelrequired'],
          xp_multiplier=dbrod['xpmultiplier'],
          min_catch=dbrod['mincatch'],
          max_catch=dbrod['maxcatch'],
          line_break_chance=dbrod['linebreakchance'],
        )
      )

    return data

  def add_rod(self, member_id: int, guild_id: int, rod_id: int):
    cursor = self.connection.cursor()

    cursor.execute("""
      INSERT OR IGNORE INTO memberrod (memberid, guildid, rodid) VALUES (?, ?, ?);
    """, (member_id, guild_id, rod_id))

    self.connection.commit()

  def equip_rod(self, member_id: int, guild_id: int, rod_id: int):
    cursor = self.connection.cursor()

    cursor.execute("""
      UPDATE guildmember SET rodid = ? WHERE memberid = ? AND guildid = ?;
    """, (rod_id, member_id, guild_id))

    self.connection.commit()

  def update_user(self, guild_id: int, member_id: int, user: FUser) -> None:
    query = """
      UPDATE guildmember
      SET
        coins = ?,
        xp = ?,
        xpstep = ?,
        xpnext = ?,
        level = ?,
        lastclaimed = ?,
        fishingcooldown = ?
      WHERE guildid = ? AND memberid = ?;
    """
    params = (
      user.coins,
      user.xp,
      user.xp_step,
      user.xp_next,
      user.level,
      user.lastclaimed.strftime('%Y-%m-%d %H:%M:%S'),
      user.fishing_cooldown,
      guild_id,
      member_id,
    )

    with self.connection:
      self.connection.execute(query, params)

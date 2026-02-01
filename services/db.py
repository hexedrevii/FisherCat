import sqlite3
import math

from models.area import Area
from models.fish import Fish
from models.fuser import FUser
from datetime import datetime

from models.rarity import Rarity
from models.rod import Rod

from datetime import datetime, timedelta


class DbService:
  def __init__(self, connection: sqlite3.Connection):
      self.connection = connection

      self.DAILY_BONUS_COINS = 500
      self.DAILY_XP_BONUS = 100

      self.LEVEL_INCREASE: float = 0.15
      self.LEVEL_GAP: float = 2.0

      self.COIN_REWARD: int = 50
      self.COIN_REWARD_INCREASE: float = 12.7


  def ensure_guild(self, guild_id: int) -> None:
    '''
    Enrolls a guild in the database.
    '''
    try:
      cursor = self.connection.cursor()

      # Check if the guild is already there.
      guild_exists = cursor.execute("SELECT * FROM guild WHERE id = ?", (guild_id,)).fetchone()
      if not guild_exists is None:
          return

      cursor.execute("INSERT OR IGNORE INTO guild (id) VALUES (?)", (guild_id,))
      self.connection.commit()

      print("Enrolled guild: ", guild_id)
    except Exception as e:
      print(f"Error enrolling guild {guild_id}: {e}")


  def ensure_user(self, member_id: int, guild_id: int) -> FUser|None:
    '''
    Add user to the database if not already present.
    '''
    try:
      cursor = self.connection.cursor()

      result = cursor.execute("""
        SELECT * FROM guildmember WHERE guildid = ? AND memberid = ?;
      """, (guild_id, member_id)).fetchone()

      if result is not None:
        # User exists, we just fill up the fuser and bail.
        db_user = FUser()

        db_user.coins = result['coins']

        db_user.xp = result['xp']
        db_user.xp_step = result['xpstep']
        db_user.xp_next = result['xpnext']

        db_user.level = result['level']

        db_user.lastclaimed = datetime.strptime(result['lastclaimed'], '%Y-%m-%d %H:%M:%S')
        db_user.fishing_cooldown = result['fishingcooldown']

        return db_user

      # User does not exist, we enroll them.
      cursor.execute("""
        INSERT INTO member (id) VALUES (?);
      """, (member_id,))

      cursor.execute("""
        INSERT INTO guildmember (guildid, memberid) VALUES (?, ?) ON CONFLICT DO NOTHING;
      """, (guild_id, member_id))

      self.connection.commit()

      return FUser()
    except Exception as e:
      print(f"Error enrolling user {member_id} in guild {guild_id}: {e}")


  def add_xp(self, guild_id: int, member_id: int, xp: int, user: FUser) -> tuple[int, int]:
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

        if user.level % 5 == 0:
          user.xp_step += 5

        user.xp_next = math.floor(math.pow(user.level / self.LEVEL_INCREASE, self.LEVEL_GAP))

    self.update_user(guild_id= guild_id, member_id= member_id, user= user)

    return (total_levels, total_coins)


  def add_fish(self, guild_id: int, member_id: int, fish_id: int, fish_amount: int = 1) -> None:
    '''
    Update player inventory with new fish.
    '''

    try:
      cursor = self.connection.cursor()
      cursor.execute(fr"""
      INSERT INTO inventory (guildid, memberid, fishid, amount) VALUES (?, ?, ?, ?)
      ON CONFLICT(guildid, memberid, fishid) DO UPDATE SET amount = amount + {fish_amount};
      """, (guild_id, member_id, fish_id, fish_amount))

      self.connection.commit()
    except Exception as e:
       print(f"Error adding fish {fish_id} to member {member_id} in guild {guild_id}: {e}")


  def get_all_user_fish(self, guild_id: int, member_id: int) -> list[(Fish, int)]:
    '''
      Returns a list of tuples, containing the fish on the left and the amount of it on the right.
    '''

    try:
      cursor = self.connection.cursor()
      cursor.execute('''
        SELECT * FROM inventory
        WHERE guildid = ? AND memberid = ?;
      ''', (guild_id, member_id))

      rows = cursor.fetchall()
      fish_data: list[(Fish, int)] = []

      for row in rows:
        fish_id = row['fishid']
        fish_amount = row['amount']

        cursor.execute("SELECT id, name, xp, rarity, odds, area, base_value FROM fish WHERE id = ?", (fish_id,))
        fish_row = cursor.fetchone()

        fish = Fish(
          id=fish_row['id'],
          name=fish_row['name'],
          xp=fish_row['xp'],
          rarity=Rarity[fish_row['rarity']],
          odds=fish_row['odds'],
          area=Area[fish_row['area']],
          base_value=fish_row['base_value']
        )

        fish_data.append((fish, fish_amount))

      return fish_data
    except Exception as e:
      print(f'Error fetching fish from user {member_id} in {guild_id}: {e}')


  def get_user_fish(self, guild_id: int, member_id: int, fish_id: int) -> tuple[Fish, int]:
    try:
      cursor = self.connection.cursor()
      cursor.execute('''
        SELECT i.*, f.* FROM inventory i
        INNER JOIN fish f ON i.fishid = f.id
        WHERE i.memberid = ? AND i.guildid = ? AND i.fishid = ?;
        ''', (member_id, guild_id, fish_id)
      )

      row = cursor.fetchone()
      fish = Fish(
        id=row['id'],
        name=row['name'],
        xp=row['xp'],
        rarity=Rarity[row['rarity']],
        odds=row['odds'],
        area=Area[row['area']],
        base_value=row['base_value']
      )

      return (fish, row['amount'])
    except Exception as e:
      print(f'Error fetching fish from user {member_id} in {guild_id}: {e}')


  def update_user_fish(self, member_id: int, guild_id: int, fish_id: int, count: int):
    try:
      cursor = self.connection.cursor()

      if count == 0:
        cursor.execute('''
          DELETE FROM inventory
          WHERE fishid = ? AND memberid = ? AND guildid = ?
        ''', (fish_id, member_id, guild_id))
      else:
        cursor.execute('''
          UPDATE inventory
          SET amount = ?
          WHERE fishid = ? AND memberid = ? AND guildid = ?;
        ''', (count, fish_id, member_id, guild_id))

      self.connection.commit()
    except Exception as e:
      print(f'Error updating fish from user {member_id} in {guild_id} for fish {fish_id}: {e}')


  def get_user_rod(self, member_id: int, guild_id: int) -> Rod|None:
    try:
      cursor = self.connection.cursor()

      query = """
        SELECT
          r.id, r.name, r.value, r.mincatch, r.maxcatch, r.linebreakchance
        FROM guildmember gm
        JOIN rod r ON gm.rodid = r.id
        WHERE gm.memberid = ? AND gm.guildid = ?
      """

      cursor.execute(query, (member_id, guild_id))

      dbrod = cursor.fetchone()
      if dbrod is None: return None

      return Rod(
        id=dbrod['id'],
        name=dbrod['name'],
        value=dbrod['value'],
        min_catch=dbrod['mincatch'], max_catch=dbrod['maxcatch'],
        line_break_chance=dbrod['linebreakchance']
      )
    except Exception as e:
      print(f'Error fetching rod from user {member_id} in guild {guild_id}: {e}')
      return None


  def update_user(self, guild_id: int, member_id: int, user: FUser):
    try:
      cursor = self.connection.cursor()

      cursor.execute('''
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
      ''', (user.coins, user.xp, user.xp_step, user.xp_next, user.level, user.lastclaimed.strftime('%Y-%m-%d %H:%M:%S'), user.fishing_cooldown, guild_id, member_id))

      self.connection.commit()
    except Exception as e:
      print(f"Error updating user: {e}")

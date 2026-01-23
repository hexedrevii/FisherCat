import sqlite3
from models.fuser import FUser
from datetime import datetime

class DbService:
  def __init__(self, connection: sqlite3.Connection):
      self.connection = connection


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

import sqlite3
import sys
import json

from models.area import Area
from models.fish import Fish
from models.rarity import Rarity
from models.rod import Rod
from services.fish_service import FishService
from util.weighted_random import WeightedRandom

import logging


LOGGER = logging.getLogger('FisherCat.DatabaseInitialisation')


def drop_tables(conn: sqlite3.Connection) -> bool:
  """
  Drops all tables in the database. This is ONLY meant for the development branch, and should not be called in production.
  """

  if not conn:
    LOGGER.error('No connection provided.', file=sys.stderr)
    return False

  try:
    cursor = conn.cursor()
    cursor.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';"
    )
    tables = cursor.fetchall()

    for table_name in tables:
      cursor.execute(f'DROP TABLE IF EXISTS {table_name[0]};')

    conn.commit()
    return True
  except sqlite3.Error as e:
    LOGGER.error(f'Failed to drop tables: {e}')
    return False


def initialize_database(conn: sqlite3.Connection) -> bool:
  if not conn:
    LOGGER.error('No connection provided.')
    return False

  try:
    cursor = conn.cursor()

    cursor.execute('PRAGMA foreign_keys = ON;')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild (
            id INTEGER PRIMARY KEY
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS member (
            id INTEGER PRIMARY KEY
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fish (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            xp INTEGER NOR NULL,
            rarity INTEGER NOT NULL,
            odds INTEGER NOT NULL,
            area TEXT NOT NULL,
            base_value INTEGER NOT NULL
        );
    """)

    cursor.execute("""
      CREATE TABLE IF NOT EXISTS rod (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,

        value INTEGER NOT NULL,
        levelrequired INTEGER NOT NULL,
        xpmultiplier REAL NOT NULL,

        mincatch INTEGER NOT NULL,
        maxcatch INTEGER NOT NULL,

        linebreakchance INTEGER NOR NULL
      );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guildmember (
            guildid INTEGER NOT NULL,
            memberid INTEGER NOT NULL,
            rodid INTEGER NOT NULL DEFAULT 1,

            coins INTEGER DEFAULT 0,

            xp INTEGER DEFAULT 0,
            xpstep INTEGER DEFAULT 1,
            xpnext INTEGER DEFAULT 30,

            level INTEGER DEFAULT 1,

            lastclaimed TEXT DEFAULT '1970-01-01 02:00:00',

            fishingcooldown INTEGER DEFAULT 15,

            PRIMARY KEY (guildid, memberid),

            FOREIGN KEY (guildid) REFERENCES guild(id) ON DELETE CASCADE,
            FOREIGN KEY (memberid) REFERENCES member(id) ON DELETE CASCADE,

            FOREIGN KEY (rodid) REFERENCES rod(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
      CREATE TABLE IF NOT EXISTS inventory (
          guildid INTEGER NOT NULL,
          memberid INTEGER NOT NULL,
          fishid INTEGER NOT NULL,
          amount INTEGER DEFAULT 0,

          PRIMARY KEY (guildid, memberid, fishid),
          FOREIGN KEY (guildid, memberid) REFERENCES guildmember(guildid, memberid) ON DELETE CASCADE,
          FOREIGN KEY (fishid) REFERENCES fish(id) ON DELETE CASCADE
      );
    """)

    conn.commit()
    LOGGER.info('Tables created successfully.')
    return True

  except sqlite3.Error as e:
    LOGGER.error(f'Could not create default tables: {e}')
    return False


def import_fish(conn: sqlite3.Connection, fish_service: FishService):
  if not conn:
    LOGGER.error('No connection provided.')
    return False

  try:
    with open('./data/fish.json', 'r') as f:
      fish_data = json.load(f)
  except FileNotFoundError:
    LOGGER.error('fish.json not found.')
    return False

  cursor = conn.cursor()

  try:
    for f in fish_data['fish_data']:
      cursor.execute(
        """
        INSERT INTO fish (name, xp, rarity, odds, area, base_value)
        VALUES (?, ?, ?, ?, ?, ?);
      """,
        (f['name'], f['xp'], f['rarity'], f['odds'], f['area'], f['base_value']),
      )

      generated_id = cursor.lastrowid
      if generated_id is None:
        return False

      fish = Fish(
        id=generated_id,
        name=f['name'],
        xp=f['xp'],
        rarity=Rarity[f['rarity']],
        odds=f['odds'],
        area=Area[f['area']],
        base_value=f['base_value'],
      )

      fish_service.fish.append(fish)

      fish_area: WeightedRandom = getattr(fish_service, fish.area.name)
      try:
        fish_area.add(fish, 1 / fish.odds)
      except ValueError as e:
        LOGGER.error(
          f'Failed adding fish {fish.name} (1/{fish.odds}) to {fish.area.name}: {e}'
        )
        sys.exit(1)
    conn.commit()
    LOGGER.info(f'Successfully imported {len(fish_data["fish_data"])} fish.')
    return True

  except sqlite3.Error as e:
    LOGGER.error(f'Database error during import: {e}')
    return False
  except KeyError as e:
    LOGGER.error(f'JSON Data Error: Missing key {e}')
    return False


def load_existing_fish(conn: sqlite3.Connection, fish_service: FishService) -> bool:
  if not conn:
    LOGGER.error('No connection provided.')
    return False

  cursor = conn.cursor()

  try:
    cursor.execute('SELECT id, name, xp, rarity, odds, area, base_value FROM fish')
    rows = cursor.fetchall()

    count = 0
    for row in rows:
      db_id, name, xp, rarity_str, odds, area_str, base_value = row

      fish = Fish(
        id=db_id,
        name=name,
        xp=xp,
        rarity=Rarity[rarity_str],
        odds=odds,
        area=Area[area_str],
        base_value=base_value,
      )

      fish_service.fish.append(fish)

      if hasattr(fish_service, fish.area.name):
        fish_area: WeightedRandom = getattr(fish_service, fish.area.name)

        try:
          fish_area.add(fish, 1 / fish.odds)
        except ValueError as e:
          LOGGER.error(
            f'Failed adding fish {fish.name} (1/{fish.odds}) to {fish.area.name}: {e}'
          )
          sys.exit(1)
      else:
        LOGGER.warning(f"FishService missing area attribute '{fish.area.name}'")

      count += 1

    LOGGER.info(f'Successfully loaded {count} fish from database into memory.')
    return True

  except sqlite3.Error as e:
    LOGGER.error(f'Database error during fish load: {e}')
    return False
  except KeyError as e:
    LOGGER.error(f'Enum Conversion Error: Database contains invalid key {e}')
    return False


def import_rods(conn: sqlite3.Connection, fish_service: FishService) -> bool:
  if not conn:
    LOGGER.error('No connection provided.')
    return False

  try:
    with open('./data/rods.json', 'r') as f:
      rod_data = json.load(f)
  except FileNotFoundError:
    LOGGER.error('rods.json not found.')
    return False

  cursor = conn.cursor()

  try:
    for r in rod_data['rod_data']:
      cursor.execute(
        """
        INSERT INTO rod (name, description, value, levelrequired, xpmultiplier, mincatch, maxcatch, linebreakchance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      """,
        (
          r['name'],
          r['description'],
          r['value'],
          r['level_required'],
          r['xp_multiplier'],
          r['min_catch'],
          r['max_catch'],
          r['line_break_chance'],
        ),
      )

      generated_id = cursor.lastrowid
      if generated_id is None:
        return False

      fish_service.rods.append(
        Rod(
          id=generated_id,
          name=r['name'],
          description=r['description'],
          value=r['value'],
          level_required=r['level_required'],
          xp_multiplier=r['xp_multiplier'],
          max_catch=r['max_catch'],
          min_catch=r['min_catch'],
          line_break_chance=r['line_break_chance'],
        )
      )

    conn.commit()
    LOGGER.info(f'Sucessfully imported {len(rod_data["rod_data"])} rods.')
    return True
  except sqlite3.Error as e:
    LOGGER.error(f'Database error rod during load: {e}')
    return False


def load_existing_rods(conn: sqlite3.Connection, fish_service: FishService):
  if not conn:
    LOGGER.error('No connection provided.')
    return False

  cursor = conn.cursor()
  try:
    cursor.execute(
      'SELECT id, name, description, value, levelrequired, xpmultiplier, mincatch, maxcatch, linebreakchance FROM rod;'
    )
    rows = cursor.fetchall()

    count = 0
    for row in rows:
      (
        db_id,
        name,
        description,
        value,
        level_required,
        xp_multiplier,
        min_catch,
        max_catch,
        line_break_chance,
      ) = row

      fish_service.rods.append(
        Rod(
          id=db_id,
          name=name,
          description=description,
          value=value,
          level_required=level_required,
          xp_multiplier=xp_multiplier,
          min_catch=min_catch,
          max_catch=max_catch,
          line_break_chance=line_break_chance,
        )
      )

      count += 1

    LOGGER.info(f'Sucessfully imported {count} rods.')
    return True

  except sqlite3.Error as e:
    LOGGER.error(f'Error importing rods: {e}')
    return False

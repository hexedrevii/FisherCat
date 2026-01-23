import sqlite3
import sys
import json

from models.area import Area
from models.fish import Fish
from models.rarity import Rarity
from services.fish_service import FishService
from util.weighted_random import WeightedRandom


def drop_tables(conn: sqlite3.Connection):
  '''
    Drops all tables in the database. This is ONLY meant for the development branch, and should not be called in production.
  '''

  if not conn:
    print('ERROR: No connection provided.', file=sys.stderr)
    return False

  try:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tables = cursor.fetchall()

    for table_name in tables:
      cursor.execute(f'DROP TABLE IF EXISTS {table_name[0]};')
      print(f'Dropped table: {table_name[0]}')

    conn.commit()
    return True
  except sqlite3.Error as e:
    print(f'ERROR: Failed to drop tables: {e}', file=sys.stderr)
    return False


def initialize_database(conn: sqlite3.Connection):
  if not conn:
    print("ERROR: No connection provided.", file=sys.stderr)
    return False

  try:
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

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
            rarity INTEGER NOT NULL,
            odds INTEGER NOT NULL,
            area TEXT NOT NULL,
            base_value INTEGER NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guildmember (
            guildid INTEGER NOT NULL,
            memberid INTEGER NOT NULL,

            coins INTEGER DEFAULT 0,

            xp INTEGER DEFAULT 0,
            xpstep INTEGER DEFAULT 1,
            xpnext INTEGER DEFAULT 30,

            level INTEGER DEFAULT 1,

            lastclaimed TEXT DEFAULT '1970-01-01 02:00:00',

            fishingcooldown INTEGER DEFAULT 15,

            PRIMARY KEY (guildid, memberid),
            FOREIGN KEY (guildid) REFERENCES guild(id) ON DELETE CASCADE,
            FOREIGN KEY (memberid) REFERENCES member(id) ON DELETE CASCADE
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
    print("Tables created successfully.")
    return True

  except sqlite3.Error as e:
    print(f"ERROR: Could not create default tables: {e}", file=sys.stderr)
    return False


def import_fish(conn: sqlite3.Connection, fish_service: FishService):
  if not conn:
    print("ERROR: No connection provided.", file=sys.stderr)
    return False

  try:
    with open('./data/fish.json', 'r') as f:
      fish_data = json.load(f)
  except FileNotFoundError:
    print("ERROR: fish.json not found.", file=sys.stderr)
    return False

  cursor = conn.cursor()

  try:
    for f in fish_data['fish_data']:
      cursor.execute("""
        INSERT INTO fish (name, rarity, odds, area, base_value)
        VALUES (?, ?, ?, ?, ?);
      """, (f['name'], f['rarity'], f['odds'], f['area'], f['base_value']))

      generated_id = cursor.lastrowid

      fish = Fish(
        id=generated_id,
        name=f['name'],
        rarity=Rarity[f['rarity']],
        odds=f['odds'],
        area=Area[f['area']],
        base_value=f['base_value']
      )

      fish_service.fish.append(fish)

      fish_area: WeightedRandom = getattr(fish_service, fish.area.name)
      fish_area.add(fish, 1 / fish.odds)

    conn.commit()
    print(f"Successfully imported {len(fish_data['fish_data'])} fish.")
    return True

  except sqlite3.Error as e:
    print(f"Database error during import: {e}", file=sys.stderr)
    return False
  except KeyError as e:
    print(f"JSON Data Error: Missing key {e}", file=sys.stderr)
    return False
